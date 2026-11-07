"""Validate future Benchmark v2 frames and variants without running detectors."""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections import Counter, defaultdict
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Any

import yaml
from jsonschema import Draft202012Validator, FormatChecker

DEFAULT_FRAME_SCHEMA = Path("schemas/benchmark_v2_semantic_frame.schema.json")
DEFAULT_VARIANT_SCHEMA = Path("schemas/benchmark_v2_variant.schema.json")
DEFAULT_SOURCE_SCHEMA = Path("schemas/benchmark_v2_source_manifest.schema.json")
ACTIVE_URL_RE = re.compile(r"(?i)\bhttps?://")
UNSAFE_DOMAIN_RE = re.compile(r"(?i)\b(?:www\.|[a-z0-9-]+\.(?:com|org|net|io|co|us|uk|info|biz))(?:/[^\s]*)?")
EMAIL_RE = re.compile(r"(?i)\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b")
PHONE_RE = re.compile(r"(?<!\w)(?:\+?\d[\d ()-]{5,}\d)(?!\w)")
MONEY_RE = re.compile(r"(?i)(?:[$£€]\s*\d|\d+(?:[.,]\d+)?\s*(?:usd|gbp|eur|dollars?|pounds?|euros?))")


@dataclass(frozen=True)
class ValidationIssue:
    code: str
    record_id: str
    message: str


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            if not line.strip():
                continue
            try:
                value = json.loads(line)
            except json.JSONDecodeError as error:
                raise ValueError(f"{path}:{line_number}: invalid JSON: {error.msg}") from error
            if not isinstance(value, dict):
                raise ValueError(f"{path}:{line_number}: each JSONL record must be an object")
            records.append(value)
    return records


def load_schema(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _schema_issues(records: list[dict[str, Any]], schema: dict[str, Any], id_field: str) -> list[ValidationIssue]:
    validator = Draft202012Validator(schema, format_checker=FormatChecker())
    issues: list[ValidationIssue] = []
    for index, record in enumerate(records, start=1):
        record_id = str(record.get(id_field, f"row-{index}"))
        for error in sorted(validator.iter_errors(record), key=lambda item: list(item.path)):
            location = ".".join(str(part) for part in error.path) or "record"
            issues.append(ValidationIssue("schema_failure", record_id, f"{location}: {error.message}"))
    return issues


def _duplicate_issues(records: list[dict[str, Any]], field: str, code: str) -> list[ValidationIssue]:
    values = [str(record.get(field, "")) for record in records]
    return [ValidationIssue(code, value, f"{field} must be unique") for value, count in Counter(values).items() if value and count > 1]


def validate_records(
    frames: list[dict[str, Any]],
    variants: list[dict[str, Any]],
    config: dict[str, Any],
    sources: list[dict[str, Any]] | None = None,
    frame_schema: dict[str, Any] | None = None,
    variant_schema: dict[str, Any] | None = None,
    source_schema: dict[str, Any] | None = None,
) -> list[ValidationIssue]:
    frame_schema = frame_schema or load_schema(DEFAULT_FRAME_SCHEMA)
    variant_schema = variant_schema or load_schema(DEFAULT_VARIANT_SCHEMA)
    source_schema = source_schema or load_schema(DEFAULT_SOURCE_SCHEMA)
    sources = sources or []
    pool = config.get("generation", {}).get("generator_pool", {})
    pool_version = str(pool.get("version", "")).strip()
    required_generator_fields = {"generator_block_id", "provider", "model", "exact_model_version", "access_method", "supported_seed_behavior", "temperature", "structured_output_support", "assignment_weight", "status"}
    issues: list[ValidationIssue] = []
    if not pool_version:
        issues.append(ValidationIssue("invalid_generator_pool", "generator_pool", "Version is required"))
    for entry in pool.get("entries", []):
        missing_fields = sorted(required_generator_fields.difference(entry))
        if missing_fields or entry.get("status") not in {"active", "inactive"}:
            issues.append(ValidationIssue("invalid_generator_pool", str(entry.get("generator_block_id", "unknown")), f"Missing/invalid fields: {missing_fields}"))
        weight = entry.get("assignment_weight")
        if not isinstance(weight, (int, float)) or not 0 <= weight <= 1:
            issues.append(ValidationIssue("invalid_generator_pool", str(entry.get("generator_block_id", "unknown")), "assignment_weight must be in [0,1]"))
    issues += _schema_issues(frames, frame_schema, "scenario_id")
    issues += _schema_issues(variants, variant_schema, "variant_id")
    issues += _schema_issues(sources, source_schema, "source_id")
    issues += _duplicate_issues(frames, "scenario_id", "duplicate_scenario_id")
    issues += _duplicate_issues(variants, "variant_id", "duplicate_variant_id")
    issues += _duplicate_issues(sources, "source_id", "duplicate_source_id")

    frame_by_id = {str(frame.get("scenario_id")): frame for frame in frames}
    source_by_id = {str(source.get("source_id")): source for source in sources}
    for frame in frames:
        record_id = str(frame.get("scenario_id", "unknown"))
        source = source_by_id.get(str(frame.get("source_id", "")))
        if source is None:
            issues.append(ValidationIssue("unknown_source_id", record_id, "Frame has no source-manifest entry"))
        elif source.get("redistribution_status") != "permitted" or source.get("privacy_review_status") != "passed":
            issues.append(ValidationIssue("source_not_authorized", record_id, "Redistribution must be permitted and privacy review passed"))
        elif frame.get("source_type") == "transformed_real" and source.get("transformation_permission") != "permitted":
            issues.append(ValidationIssue("source_not_authorized", record_id, "Transformed-real source lacks transformation permission"))
    populations_by_scenario: dict[str, set[str]] = defaultdict(set)
    populations_by_family: dict[str, set[str]] = defaultdict(set)
    normalized_texts: dict[str, list[str]] = defaultdict(list)
    thresholds = config.get("validation", {})
    minimum = int(thresholds.get("sms_length_characters", {}).get("minimum", 10))
    maximum = int(thresholds.get("sms_length_characters", {}).get("maximum", 480))

    variant_by_id = {str(variant.get("variant_id")): variant for variant in variants}
    pool_entries = config.get("generation", {}).get("generator_pool", {}).get("entries", [])
    active_pool = {str(item.get("generator_block_id")): item for item in pool_entries if item.get("status") == "active"}
    variants_by_scenario: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for frame in frames:
        family_id = str(frame.get("scenario_family_id", ""))
        populations_by_family[family_id].add(str(frame.get("population", "")))
        target = frame.get("message_length_target", {})
        if isinstance(target, dict) and target.get("min_characters", 0) > target.get("max_characters", 0):
            issues.append(ValidationIssue("invalid_length_target", str(frame.get("scenario_id", "unknown")), "min_characters exceeds max_characters"))

    for variant in variants:
        variant_id = str(variant.get("variant_id", "unknown"))
        scenario_id = str(variant.get("scenario_id", ""))
        text = str(variant.get("text", ""))
        population = str(variant.get("population", ""))
        populations_by_scenario[scenario_id].add(population)
        variants_by_scenario[scenario_id].append(variant)
        frame = frame_by_id.get(scenario_id)
        if frame is None:
            issues.append(ValidationIssue("unknown_scenario_id", variant_id, f"No frame for {scenario_id}"))
            continue
        if population != str(frame.get("population", "")):
            issues.append(ValidationIssue("scenario_split_leakage", variant_id, "Variant population differs from its semantic frame"))
        if variant.get("label") != frame.get("label"):
            issues.append(ValidationIssue("label_changed", variant_id, "Variant label differs from semantic frame"))
        creation_method = variant.get("creation_method")
        generator_fields = ("generator_provider", "generator_model", "model_version", "temperature", "response_id")
        if creation_method != "llm_generated":
            if any(variant.get(field) is not None for field in generator_fields):
                issues.append(ValidationIssue("invalid_generator_metadata", variant_id, "Non-LLM anchors require null generator metadata"))
            if any(str(variant.get(field, "")).lower() == "not_applicable" for field in generator_fields):
                issues.append(ValidationIssue("invalid_generator_metadata", variant_id, "Use null, never invented not_applicable metadata"))
        else:
            block_id = str(variant.get("generator_block_id", ""))
            pool = active_pool.get(block_id)
            if pool is None:
                issues.append(ValidationIssue("unknown_generator_block", variant_id, "LLM generator block is not active in the versioned pool"))
            elif (variant.get("generator_provider"), variant.get("generator_model"), variant.get("model_version"), variant.get("temperature")) != (pool.get("provider"), pool.get("model"), pool.get("exact_model_version"), pool.get("temperature")):
                issues.append(ValidationIssue("generator_metadata_mismatch", variant_id, "Variant metadata differs from its generator-pool block"))
        if variant.get("condition") != "C0_template" and creation_method != "llm_generated":
            issues.append(ValidationIssue("invalid_creation_method", variant_id, "C1/C2/C3 must be llm_generated"))
        if not text.strip():
            issues.append(ValidationIssue("empty_text", variant_id, "Variant text is empty"))
        if not minimum <= len(text) <= maximum:
            issues.append(ValidationIssue("implausible_sms_length", variant_id, f"Length {len(text)} outside {minimum}..{maximum}"))
        if ACTIVE_URL_RE.search(text):
            issues.append(ValidationIssue("active_url", variant_id, "Active http(s) URL is prohibited"))
        if EMAIL_RE.search(text):
            issues.append(ValidationIssue("unexpected_email", variant_id, "Email address is prohibited"))
        domain_text = text.replace("[DEFANGED_URL]", "")
        if UNSAFE_DOMAIN_RE.search(domain_text):
            issues.append(ValidationIssue("non_defanged_domain", variant_id, "www or non-defanged domain is prohibited"))
        sanitized = text.replace("[PHONE_PLACEHOLDER]", "")
        if PHONE_RE.search(sanitized):
            issues.append(ValidationIssue("unexpected_phone_number", variant_id, "Unexpected phone-like number"))
        if MONEY_RE.search(text.replace("[AMOUNT]", "")):
            issues.append(ValidationIssue("unexpected_monetary_amount", variant_id, "Literal monetary amount is prohibited"))
        entity_placeholders = set(frame.get("entity_placeholders", []))
        invariants = set(frame.get("critical_invariants", []))
        for placeholder in entity_placeholders:
            if str(placeholder) not in text:
                issues.append(ValidationIssue("missing_entity_placeholder", variant_id, f"Missing {placeholder}"))
            if str(placeholder) not in invariants:
                issues.append(ValidationIssue("placeholder_consistency", variant_id, f"Entity {placeholder} is missing from critical_invariants"))
        placeholder_expectations = {
            "[DEFANGED_URL]": bool(frame.get("url_present")),
            "[AMOUNT]": frame.get("financial_amount_placeholder") == "[AMOUNT]",
            "[CURRENCY]": frame.get("currency_placeholder") == "[CURRENCY]",
            "[DATE]": frame.get("time_reference") == "[DATE]",
            "[PHONE_PLACEHOLDER]": "[PHONE_PLACEHOLDER]" in entity_placeholders,
            "[MERCHANT]": frame.get("merchant_placeholder") == "[MERCHANT]",
            "[REFERENCE_ID]": "[REFERENCE_ID]" in entity_placeholders,
        }
        for placeholder, expected in placeholder_expectations.items():
            present_in_text = placeholder in text
            present_in_entities = placeholder in entity_placeholders
            present_in_invariants = placeholder in invariants
            if expected and not (present_in_text and present_in_entities and present_in_invariants):
                issues.append(ValidationIssue("placeholder_consistency", variant_id, f"Expected {placeholder} in entities, invariants, and text"))
            if not expected and (present_in_text or present_in_entities or present_in_invariants):
                issues.append(ValidationIssue("unexpected_placeholder", variant_id, f"Unexpected {placeholder}"))
        normalized = " ".join(re.findall(r"\w+|\[[A-Z_]+\]", text.casefold()))
        normalized_texts[normalized].append(variant_id)

    for scenario_id, populations in populations_by_scenario.items():
        if len(populations) > 1:
            issues.append(ValidationIssue("scenario_split_leakage", scenario_id, f"Variants span populations: {sorted(populations)}"))
    for family_id, populations in populations_by_family.items():
        if family_id and len(populations) > 1:
            issues.append(ValidationIssue("scenario_family_split_leakage", family_id, f"Scenario family spans populations: {sorted(populations)}"))

    for scenario_id, scenario_variants in variants_by_scenario.items():
        by_condition = {str(item.get("condition")): item for item in scenario_variants}
        for variant in scenario_variants:
            variant_id = str(variant.get("variant_id", "unknown"))
            condition = str(variant.get("condition", ""))
            anchor = by_condition.get("C0_template")
            expected_parent = None if condition == "C0_template" else by_condition.get("C2_natural") if condition == "C3_natural_softened" else anchor
            expected_anchor_id = str(anchor.get("variant_id")) if anchor else None
            if condition == "C0_template":
                if variant.get("parent_variant_id") is not None or str(variant.get("anchor_variant_id")) != variant_id:
                    issues.append(ValidationIssue("invalid_lineage", variant_id, "C0 must be parentless and self-anchored"))
            else:
                if expected_parent is None or str(variant.get("parent_variant_id")) != str(expected_parent.get("variant_id")):
                    issues.append(ValidationIssue("invalid_lineage", variant_id, f"Invalid parent for {condition}"))
                if str(variant.get("anchor_variant_id")) != expected_anchor_id:
                    issues.append(ValidationIssue("invalid_lineage", variant_id, "Anchor must reference scenario C0"))
            for relation in (variant.get("parent_variant_id"), variant.get("anchor_variant_id")):
                if relation is not None and str(relation) not in variant_by_id:
                    issues.append(ValidationIssue("invalid_lineage", variant_id, f"Referenced variant does not exist: {relation}"))
        generated = [item for item in scenario_variants if item.get("condition") in {"C1_fluent", "C2_natural", "C3_natural_softened"}]
        generator_keys = {(item.get("generator_provider"), item.get("generator_model"), item.get("model_version"), item.get("generator_block_id")) for item in generated}
        if len(generator_keys) > 1:
            issues.append(ValidationIssue("generator_condition_confounding", scenario_id, "C1/C2/C3 must use one scenario-level generator block"))
    for ids in normalized_texts.values():
        if len(ids) > 1:
            for variant_id in ids:
                issues.append(ValidationIssue("exact_duplicate_text", variant_id, f"Duplicate text among {ids}"))
    return issues


def validate_files(frames_path: Path, variants_path: Path, sources_path: Path, config_path: Path) -> list[ValidationIssue]:
    config = yaml.safe_load(config_path.read_text(encoding="utf-8"))
    return validate_records(load_jsonl(frames_path), load_jsonl(variants_path), config, load_jsonl(sources_path))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--frames", type=Path, default=Path("data/benchmark_v2/semantic_frames.jsonl"))
    parser.add_argument("--variants", type=Path, default=Path("data/benchmark_v2/variants.jsonl"))
    parser.add_argument("--sources", type=Path, default=Path("data/benchmark_v2/source_manifest.jsonl"))
    parser.add_argument("--config", type=Path, default=Path("configs/benchmark_v2.yaml"))
    parser.add_argument("--strict", action="store_true", help="Treat missing future data as an error for CI")
    parser.add_argument("--report", type=Path, help="Optional JSON validation-report path")
    args = parser.parse_args(argv)
    missing = [path for path in (args.frames, args.variants, args.sources) if not path.exists()]
    if missing:
        message = "Benchmark v2 has not yet been generated; missing: " + ", ".join(str(path) for path in missing)
        print(message, file=sys.stderr if args.strict else sys.stdout)
        return 2 if args.strict else 0
    if not args.config.exists():
        print(f"Missing configuration: {args.config}", file=sys.stderr)
        return 2
    try:
        issues = validate_files(args.frames, args.variants, args.sources, args.config)
    except (OSError, ValueError, json.JSONDecodeError, yaml.YAMLError) as error:
        print(f"Validation could not run: {error}", file=sys.stderr)
        return 2
    report = {"valid": not issues, "issue_count": len(issues), "issues": [asdict(issue) for issue in issues]}
    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))
    return 1 if issues else 0


if __name__ == "__main__":
    raise SystemExit(main())
