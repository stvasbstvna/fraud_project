"""Strict, offline Benchmark v2 freeze-readiness audit.

The checker never generates text, calls an API, or runs a detector.  A pilot-only
artifact can satisfy an integrity check but can never authorize the final study.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
from collections import Counter, defaultdict
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_JSON = ROOT / "results/benchmark_v2/freeze_readiness.json"
DEFAULT_MD = ROOT / "results/benchmark_v2/freeze_readiness.md"
CRITICAL_FILES = (
    "configs/benchmark_v2.yaml",
    "configs/benchmark_v2_freeze_register.yaml",
    "configs/benchmark_v2_generator.yaml",
    "docs/benchmark_v2_prompt_package_draft.md",
)
REQUIRED_MODEL_IDS = {"tfidf_logistic_regression", "tfidf_random_forest"}


def _load_yaml(relative: str) -> dict:
    return yaml.safe_load((ROOT / relative).read_text(encoding="utf-8")) or {}


def _jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def _markers() -> tuple[list[dict], list[dict]]:
    tbd, todo = [], []
    for relative in CRITICAL_FILES:
        path = ROOT / relative
        if not path.exists():
            continue
        for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
            record = {"file": relative, "line": number, "text": line.strip()}
            if re.search(r"\bTBD(?:_[A-Z0-9_]+)?\b|REQUIRES_[A-Z0-9_]*(?:DECISION|APPROVAL|VERIFICATION)", line):
                tbd.append(record)
            if re.search(r"\bTODO\b", line, re.I):
                todo.append(record)
    return tbd, todo


def _pilot_integrity() -> tuple[list[str], dict]:
    errors: list[str] = []
    frame_path = ROOT / "data/benchmark_v2/pilot/semantic_frames_pilot.jsonl"
    variant_path = ROOT / "data/benchmark_v2/pilot/variants_dry_run_pilot.jsonl"
    if not frame_path.exists() or not variant_path.exists():
        return ["pilot frame or variant file is missing"], {}
    frames, variants = _jsonl(frame_path), _jsonl(variant_path)
    frame_ids = [x.get("scenario_id") for x in frames]
    variant_ids = [x.get("variant_id") for x in variants]
    if None in frame_ids or len(frame_ids) != len(set(frame_ids)):
        errors.append("missing or duplicate scenario_id")
    if None in variant_ids or len(variant_ids) != len(set(variant_ids)):
        errors.append("missing or duplicate variant_id")
    grouped: dict[str, list[str]] = defaultdict(list)
    frame_by_id = {x.get("scenario_id"): x for x in frames}
    for row in variants:
        sid = row.get("scenario_id")
        grouped[sid].append(row.get("condition"))
        frame = frame_by_id.get(sid)
        if frame is None:
            errors.append(f"variant references unknown frame: {sid}")
        elif row.get("binary_label") != frame.get("binary_label"):
            errors.append(f"label mismatch: {row.get('variant_id')}")
        if row.get("human_review_status") is None or row.get("final_benchmark_eligible") is not False:
            errors.append(f"missing review/safety eligibility metadata: {row.get('variant_id')}")
        text = str(row.get("text", ""))
        if re.search(r"https?://|\bwww\.", text, re.I):
            errors.append(f"live URL-like text: {row.get('variant_id')}")
    for sid in frame_ids:
        if Counter(grouped[sid]) != Counter(["C0", "C1", "C2", "C3"]):
            errors.append(f"incomplete conditions: {sid}")
    return sorted(set(errors)), {"frames": len(frames), "variants": len(variants)}


def _source_state() -> tuple[list[str], dict]:
    path = ROOT / "data/benchmark_v2/source_manifest.csv"
    if not path.exists():
        return ["source manifest missing"], {}
    rows = list(csv.DictReader(path.open(encoding="utf-8-sig", newline="")))
    required = {"source_id", "allowed_for_research", "allowed_for_generation", "checksum_sha256"}
    errors = []
    if not rows or not required.issubset(rows[0]):
        errors.append("manifest schema incomplete")
    authorized = [r for r in rows if r.get("allowed_for_research", "").lower() == "true" and r.get("allowed_for_generation", "").lower() == "true" and re.fullmatch(r"[0-9a-fA-F]{64}", r.get("checksum_sha256", ""))]
    if not authorized:
        errors.append("no final source has research/generation authorization and a SHA-256 checksum")
    return errors, {"sources": len(rows), "authorized_for_final_generation": len(authorized)}


def _sha_manifest_errors() -> list[str]:
    path = ROOT / "data/benchmark_v2/pilot/SHA256SUMS.json"
    if not path.exists():
        return ["pilot SHA256SUMS.json missing"]
    manifest = json.loads(path.read_text(encoding="utf-8"))
    values = manifest.get("files", manifest)
    errors = []
    for name, expected in values.items():
        candidate = path.parent / name
        if not candidate.exists() or hashlib.sha256(candidate.read_bytes()).hexdigest() != expected:
            errors.append(f"hash mismatch: {name}")
    return errors


def _review_errors() -> list[str]:
    path = ROOT / "data/benchmark_v2/pilot/human_review_queue.csv"
    if not path.exists():
        return ["pilot human-review queue missing"]
    rows = list(csv.DictReader(path.open(encoding="utf-8-sig", newline="")))
    forbidden = {"prediction", "probability", "confidence", "detector_score", "false_negative"}
    headers = {str(x).casefold() for x in (rows[0].keys() if rows else [])}
    errors = []
    leaked = sorted(forbidden & headers)
    if leaked:
        errors.append("detector-derived review fields: " + ", ".join(leaked))
    incomplete = sum(not str(row.get("decision", "")).strip() for row in rows)
    if incomplete:
        errors.append(f"{incomplete} pilot variant decisions are incomplete")
    return errors


def build_report() -> dict:
    config = _load_yaml("configs/benchmark_v2.yaml")
    register = _load_yaml("configs/benchmark_v2_freeze_register.yaml").get("benchmark_v2_pre_generation_freeze", {})
    generator = _load_yaml("configs/benchmark_v2_generator.yaml")
    tbd, todo = _markers()
    pilot_errors, pilot_counts = _pilot_integrity()
    source_errors, source_counts = _source_state()
    hash_errors = _sha_manifest_errors()
    active = [b for b in generator.get("generator_blocks", []) if b.get("status") == "active" and float(b.get("assignment_weight", 0)) > 0]
    prompt = ROOT / "docs/benchmark_v2_prompt_package_draft.md"
    draft_docs = [str(prompt.relative_to(ROOT))] if prompt.exists() and "draft" in prompt.name.casefold() else []
    draft_flags = [str(register.get("status"))] if "DO_NOT_GENERATE" in str(register.get("status", "")) else []
    analysis = config.get("analysis", {})
    analysis_errors = []
    if analysis.get("primary_outcome") != "binary phishing prediction at the detector's frozen threshold":
        analysis_errors.append("primary outcome is not frozen exactly")
    if analysis.get("confirmatory_test_count") != 7 or str(analysis.get("multiplicity_method", "")).casefold() != "holm" or analysis.get("confirmatory_familywise_alpha") != 0.05:
        analysis_errors.append("seven-test Holm family at alpha 0.05 is incomplete")
    power_json = ROOT / "results/benchmark_v2/power/power_summary.json"
    power_errors = [] if power_json.exists() else ["exact Holm sensitivity simulation output missing"]
    model_manifest = ROOT / "results/rewrite_experiment/model_hashes.csv"
    model_errors = []
    if not model_manifest.exists():
        model_errors.append("model hash manifest missing")
    else:
        content = model_manifest.read_text(encoding="utf-8-sig").casefold()
        if not all(x in content for x in REQUIRED_MODEL_IDS) or not re.search(r"[0-9a-f]{64}", content):
            model_errors.append("frozen detector identifiers/hashes incomplete")
    version_errors = [] if config.get("benchmark", {}).get("dataset_version") else ["benchmark version missing"]
    categories = {
        "unresolved_tbds": tbd,
        "unresolved_todos": todo,
        "draft_experimental_docs": draft_docs,
        "draft_do_not_generate_flags": draft_flags,
        "missing_source_authorizations": source_errors,
        "missing_generator_assignment": [] if active else ["no active positive-weight generator block"],
        "frame_variant_consistency_errors": pilot_errors,
        "hash_errors": hash_errors,
        "missing_power_analysis_outputs": power_errors,
        "missing_analysis_specifications": analysis_errors,
        "missing_model_freeze_identifiers": model_errors,
        "missing_benchmark_version": version_errors,
        "incomplete_human_review": _review_errors(),
    }
    # Technical means implemented infrastructure/integrity. Full additionally requires
    # frozen human choices, authorized sources, reviews, and removal of draft gates.
    technical_keys = {"frame_variant_consistency_errors", "hash_errors", "missing_analysis_specifications", "missing_model_freeze_identifiers", "missing_benchmark_version", "missing_power_analysis_outputs"}
    technical_ready = not any(categories[k] for k in technical_keys)
    full_ready = technical_ready and not any(categories.values())
    return {
        "benchmark_version": config.get("benchmark", {}).get("dataset_version"),
        "technical_freeze_ready": technical_ready,
        "full_freeze_ready": full_ready,
        "generation_authorized": full_ready and bool(generator.get("generation_authorized")),
        "status": "FULL_FREEZE_READY" if full_ready else ("TECHNICAL_FREEZE_READY_HUMAN_DECISIONS_PENDING" if technical_ready else "NOT_TECHNICALLY_READY"),
        "counts": {k: len(v) for k, v in categories.items()},
        "details": categories,
        "pilot_counts": pilot_counts,
        "source_counts": source_counts,
        "safety_attestation": {"messages_generated": False, "apis_called": False, "detectors_run": False},
    }


def write_report(report: dict, json_path: Path, md_path: Path) -> None:
    json_path.parent.mkdir(parents=True, exist_ok=True)
    json_path.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    lines = ["# Benchmark v2 freeze readiness", "", f"**Status:** `{report['status']}`", "", "| Check | Count |", "|---|---:|"]
    lines += [f"| {name.replace('_', ' ')} | {count} |" for name, count in report["counts"].items()]
    lines += ["", f"Technical freeze ready: **{report['technical_freeze_ready']}**", f"Full freeze ready: **{report['full_freeze_ready']}**", f"Generation authorized: **{report['generation_authorized']}**", "", "Pilot integrity is not evidence of final source authorization or completed human review."]
    md_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json-output", type=Path, default=DEFAULT_JSON)
    parser.add_argument("--markdown-output", type=Path, default=DEFAULT_MD)
    args = parser.parse_args(argv)
    report = build_report()
    write_report(report, args.json_output, args.markdown_output)
    print("BENCHMARK V2 FREEZE READINESS\n=============================")
    for key, value in report["counts"].items():
        print(f"{key.replace('_', ' ').title():40} {value}")
    print(f"\nSTATUS: {report['status']}")
    return 0 if report["technical_freeze_ready"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
