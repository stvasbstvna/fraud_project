from __future__ import annotations

import copy
import hashlib
import io
import tempfile
import unittest
from contextlib import redirect_stdout, redirect_stderr
from pathlib import Path

import yaml
from jsonschema import Draft202012Validator

from src.validate_benchmark_v2 import load_schema, main, validate_records

ROOT = Path(__file__).resolve().parents[1]
FRAME_SCHEMA = load_schema(ROOT / "schemas/benchmark_v2_semantic_frame.schema.json")
VARIANT_SCHEMA = load_schema(ROOT / "schemas/benchmark_v2_variant.schema.json")
REVIEW_SCHEMA = load_schema(ROOT / "schemas/benchmark_v2_review.schema.json")
SOURCE_SCHEMA = load_schema(ROOT / "schemas/benchmark_v2_source_manifest.schema.json")
CONFIG = yaml.safe_load((ROOT / "configs/benchmark_v2.yaml").read_text(encoding="utf-8"))
CONFIG["generation"]["generator_pool"]["entries"] = [{"generator_block_id": "GB-001", "provider": "test-provider", "model": "test-model", "exact_model_version": "test-version", "access_method": "local-test", "supported_seed_behavior": "deterministic", "temperature": 0, "structured_output_support": True, "assignment_weight": 1.0, "status": "active"}]


def valid_source() -> dict:
    return {"source_id": "BV2-SRC-0001", "source_url_or_reference": "self-authored test fixture", "access_date": "2026-08-27", "source_sha256": "a" * 64, "license_name": "self-authored", "license_url": None, "redistribution_status": "permitted", "transformation_permission": "not_applicable_self_authored", "privacy_review_status": "passed", "attribution_requirement": "none"}


def valid_frame() -> dict:
    return {
        "scenario_id": "BV2-S000001", "scenario_family_id": "BV2-F000001",
        "population": "confirmatory_final_test", "label": "phishing", "source_id": "BV2-SRC-0001",
        "source_type": "fully_synthetic", "source_reference": "protocol-fixture",
        "banking_event": "unusual_transaction", "sender_role": "bank",
        "canonical_intent": "notify about a transaction and request review",
        "communicative_goal": "request_review",
        "scenario_facts": {"event": "transaction review"},
        "critical_invariants": ["[BANK]", "[AMOUNT]"],
        "requested_action": "review_information", "action_channel": "message_only",
        "requested_information_type": "transaction_confirmation",
        "entity_placeholders": ["[BANK]", "[AMOUNT]"],
        "merchant_placeholder": None, "financial_amount_placeholder": "[AMOUNT]",
        "currency_placeholder": None, "time_reference": "none",
        "transaction_type": "purchase", "transaction_status": "pending",
        "account_card_context": "account",
        "url_present": False, "url_placeholder": None, "tactic": "authority",
        "urgency_level": "low", "personalization_level": "none",
        "message_length_target": {"min_characters": 20, "max_characters": 200},
        "language": "en-US", "country_context": "US",
        "provenance": "test fixture", "license": "synthetic-test-only",
        "created_at_utc": "2026-08-27T12:00:00Z",
    }


def valid_variant() -> dict:
    return {
        "variant_id": "BV2-V000001-C0-R01", "scenario_id": "BV2-S000001",
        "population": "confirmatory_final_test", "condition": "C0_template", "replicate_id": 1,
        "creation_method": "deterministic_template_anchor",
        "parent_variant_id": None, "anchor_variant_id": "BV2-V000001-C0-R01",
        "transformation_id": "anchor-template-v1",
        "transformation_factors": {"fluency": "anchor", "lexical_variation": "none", "syntactic_variation": "none", "conversational_naturalness": "template", "action_explicitness": "anchor", "urgency_changed": False, "personalization_changed": False},
        "generator_block_id": None,
        "text": "[BANK] notice: review the [AMOUNT] transaction information.",
        "label": "phishing", "generator_provider": None,
        "generator_model": None, "model_version": None,
        "prompt_id": "P-C0", "prompt_version": "1.0", "temperature": None,
        "seed": 1, "response_id": None, "generated_at_utc": "2026-08-27T12:00:00Z",
        "validation_status": "pending", "human_review_status": "pending",
        "exclusion_reason": None, "generation_metadata": {},
    }


def as_llm(variant: dict) -> dict:
    variant.update({"creation_method": "llm_generated", "generator_block_id": "GB-001", "generator_provider": "test-provider", "generator_model": "test-model", "model_version": "test-version", "temperature": 0, "response_id": "response-test"})
    return variant


class BenchmarkV2ValidationTests(unittest.TestCase):
    def issues(self, frames=None, variants=None, sources=None):
        return validate_records(frames or [valid_frame()], variants or [valid_variant()], CONFIG, sources=sources or [valid_source()], frame_schema=FRAME_SCHEMA, variant_schema=VARIANT_SCHEMA, source_schema=SOURCE_SCHEMA)

    def test_valid_semantic_frame_and_variant(self) -> None:
        self.assertEqual(self.issues(), [])

    def test_invalid_label(self) -> None:
        frame = valid_frame(); frame["label"] = "unknown"
        self.assertIn("schema_failure", {issue.code for issue in self.issues([frame])})

    def test_invalid_condition(self) -> None:
        variant = valid_variant(); variant["condition"] = "C9_evasive"
        self.assertIn("schema_failure", {issue.code for issue in self.issues(variants=[variant])})

    def test_active_url_rejected(self) -> None:
        variant = valid_variant(); variant["text"] += " https://example.com"
        codes = {issue.code for issue in self.issues(variants=[variant])}
        self.assertIn("active_url", codes)

    def test_unexpected_phone_rejected(self) -> None:
        variant = valid_variant(); variant["text"] += " Call 312-555-0199."
        self.assertIn("unexpected_phone_number", {issue.code for issue in self.issues(variants=[variant])})

    def test_missing_entity_placeholder(self) -> None:
        variant = valid_variant(); variant["text"] = "Review the [AMOUNT] transaction information."
        self.assertIn("missing_entity_placeholder", {issue.code for issue in self.issues(variants=[variant])})

    def test_duplicate_scenario_and_variant_ids(self) -> None:
        codes = {issue.code for issue in self.issues([valid_frame(), copy.deepcopy(valid_frame())], [valid_variant(), copy.deepcopy(valid_variant())])}
        self.assertIn("duplicate_scenario_id", codes)
        self.assertIn("duplicate_variant_id", codes)

    def test_scenario_split_leakage_and_variant_grouping(self) -> None:
        second = valid_variant()
        second["variant_id"] = "BV2-V000001-C1-R01"
        second["condition"] = "C1_fluent"
        second["population"] = "quality_validation"
        second["text"] = "Please review information about the [AMOUNT] [BANK] transaction."
        codes = {issue.code for issue in self.issues(variants=[valid_variant(), second])}
        self.assertIn("scenario_split_leakage", codes)

    def test_minimum_length_must_not_exceed_maximum(self) -> None:
        frame = valid_frame(); frame["message_length_target"] = {"min_characters": 200, "max_characters": 20}
        self.assertIn("invalid_length_target", {issue.code for issue in self.issues([frame])})

    def test_url_placeholder_symmetry_and_unsafe_destinations(self) -> None:
        frame = valid_frame(); frame["url_present"] = True; frame["url_placeholder"] = "[DEFANGED_URL]"
        frame["entity_placeholders"].append("[DEFANGED_URL]"); frame["critical_invariants"].append("[DEFANGED_URL]")
        variant = valid_variant(); variant["text"] += " [DEFANGED_URL]"
        self.assertNotIn("placeholder_consistency", {issue.code for issue in self.issues([frame], [variant])})
        variant["text"] += " www.example.com user@example.com"
        codes = {issue.code for issue in self.issues([frame], [variant])}
        self.assertIn("non_defanged_domain", codes)
        self.assertIn("unexpected_email", codes)

    def test_url_absent_forbids_defanged_placeholder(self) -> None:
        variant = valid_variant(); variant["text"] += " [DEFANGED_URL]"
        self.assertIn("unexpected_placeholder", {issue.code for issue in self.issues(variants=[variant])})

    def test_parent_anchor_lineage(self) -> None:
        c0 = valid_variant()
        c2 = as_llm(valid_variant()); c2.update({"variant_id": "BV2-V000001-C2-R01", "condition": "C2_natural", "parent_variant_id": c0["variant_id"], "anchor_variant_id": c0["variant_id"], "transformation_id": "natural-v1"})
        c2["transformation_factors"] = {"fluency": "natural", "lexical_variation": "meaningful", "syntactic_variation": "meaningful", "conversational_naturalness": "natural", "action_explicitness": "unchanged", "urgency_changed": False, "personalization_changed": False}
        c2["text"] = "Please review the [BANK] purchase of [AMOUNT]."
        c3 = copy.deepcopy(c2); c3.update({"variant_id": "BV2-V000001-C3-R01", "condition": "C3_natural_softened", "parent_variant_id": c2["variant_id"], "transformation_id": "soften-v1"})
        c3["transformation_factors"]["action_explicitness"] = "softened"; c3["text"] = "You may wish to review the [BANK] purchase of [AMOUNT]."
        self.assertNotIn("invalid_lineage", {issue.code for issue in self.issues(variants=[c0, c2, c3])})
        c3["parent_variant_id"] = c0["variant_id"]
        self.assertIn("invalid_lineage", {issue.code for issue in self.issues(variants=[c0, c2, c3])})

    def test_scenario_family_population_integrity(self) -> None:
        other = valid_frame(); other["scenario_id"] = "BV2-S000002"; other["population"] = "quality_validation"
        codes = {issue.code for issue in self.issues([valid_frame(), other], [valid_variant()])}
        self.assertIn("scenario_family_split_leakage", codes)

    def test_generator_assignment_cannot_be_confounded_with_condition(self) -> None:
        c0 = valid_variant()
        c1 = as_llm(copy.deepcopy(c0)); c1.update({"variant_id": "BV2-V000001-C1-R01", "condition": "C1_fluent", "parent_variant_id": c0["variant_id"], "anchor_variant_id": c0["variant_id"], "transformation_id": "correct-v1", "text": "Please review the [BANK] [AMOUNT] transaction."})
        c1["transformation_factors"].update({"fluency": "corrected", "lexical_variation": "minimal", "syntactic_variation": "minimal", "conversational_naturalness": "limited", "action_explicitness": "unchanged"})
        c2 = copy.deepcopy(c1); c2.update({"variant_id": "BV2-V000001-C2-R01", "condition": "C2_natural", "generator_model": "different-model", "transformation_id": "natural-v1", "text": "Take a look at the [AMOUNT] [BANK] transaction."})
        c2["transformation_factors"].update({"fluency": "natural", "lexical_variation": "meaningful", "syntactic_variation": "meaningful", "conversational_naturalness": "natural"})
        self.assertIn("generator_condition_confounding", {issue.code for issue in self.issues(variants=[c0, c1, c2])})

    def test_merchant_placeholder_requires_entities_invariants_and_text(self) -> None:
        frame = valid_frame(); frame["merchant_placeholder"] = "[MERCHANT]"
        variant = valid_variant()
        self.assertIn("placeholder_consistency", {issue.code for issue in self.issues([frame], [variant])})

    def test_date_phone_currency_and_reference_placeholder_symmetry(self) -> None:
        frame = valid_frame()
        frame.update({"time_reference": "[DATE]", "currency_placeholder": "[CURRENCY]"})
        frame["entity_placeholders"] += ["[DATE]", "[CURRENCY]", "[PHONE_PLACEHOLDER]", "[REFERENCE_ID]"]
        frame["critical_invariants"] += ["[DATE]", "[CURRENCY]", "[PHONE_PLACEHOLDER]", "[REFERENCE_ID]"]
        variant = valid_variant()
        variant["text"] += " [DATE] [CURRENCY] [PHONE_PLACEHOLDER] [REFERENCE_ID]"
        codes = {issue.code for issue in self.issues([frame], [variant])}
        self.assertNotIn("placeholder_consistency", codes)
        variant["text"] = variant["text"].replace("[REFERENCE_ID]", "")
        self.assertIn("missing_entity_placeholder", {issue.code for issue in self.issues([frame], [variant])})

    def test_review_schema_accepts_complete_review(self) -> None:
        review = {"review_id": "BV2-REV-00000001", "variant_id": "BV2-V000001-C0-R01", "blinded_reviewer_id": "R-01", "semantic_intent_decision": "yes", "requested_action_decision": "yes", "action_channel_decision": "yes", "label_decision": "yes", "entity_fact_decision": "yes", "operational_safety_decision": "yes", "condition_fit_decision": "yes", "naturalness_rating": 3, "action_explicitness_rating": 5, "overall_decision": "approved", "rejection_reason": None, "notes": "", "reviewed_at_utc": "2026-08-27T12:00:00Z", "adjudication_metadata": {"is_adjudication": False, "adjudicator_id": None, "source_review_ids": [], "rating_tie": False, "aggregation_rule_version": None, "adjudicated_at_utc": None}}
        self.assertEqual(list(Draft202012Validator(REVIEW_SCHEMA).iter_errors(review)), [])

    def test_non_llm_anchor_requires_null_not_not_applicable_metadata(self) -> None:
        variant = valid_variant(); variant["generator_model"] = "not_applicable"
        self.assertIn("invalid_generator_metadata", {issue.code for issue in self.issues(variants=[variant])})

    def test_llm_variant_must_match_active_versioned_generator_block(self) -> None:
        c0 = valid_variant()
        c1 = as_llm(copy.deepcopy(c0)); c1.update({"variant_id": "BV2-V000001-C1-R01", "condition": "C1_fluent", "parent_variant_id": c0["variant_id"], "anchor_variant_id": c0["variant_id"], "text": "Please review the [BANK] transaction of [AMOUNT]."})
        self.assertNotIn("generator_metadata_mismatch", {issue.code for issue in self.issues(variants=[c0, c1])})
        c1["model_version"] = "invented-version"
        self.assertIn("generator_metadata_mismatch", {issue.code for issue in self.issues(variants=[c0, c1])})

    def test_generator_pool_requires_versioned_complete_entries(self) -> None:
        broken = copy.deepcopy(CONFIG); broken["generation"]["generator_pool"]["version"] = ""; del broken["generation"]["generator_pool"]["entries"][0]["access_method"]
        issues = validate_records([valid_frame()], [valid_variant()], broken, sources=[valid_source()], frame_schema=FRAME_SCHEMA, variant_schema=VARIANT_SCHEMA, source_schema=SOURCE_SCHEMA)
        self.assertIn("invalid_generator_pool", {issue.code for issue in issues})

    def test_source_manifest_authorization_is_required(self) -> None:
        denied = valid_source(); denied["redistribution_status"] = "unverified"
        self.assertIn("source_not_authorized", {issue.code for issue in self.issues(sources=[denied])})
        self.assertIn("unknown_source_id", {issue.code for issue in self.issues(sources=[{"source_id": "BV2-SRC-9999"}])})

    def test_transformed_real_requires_transformation_permission(self) -> None:
        frame = valid_frame(); frame["source_type"] = "transformed_real"
        source = valid_source(); source["transformation_permission"] = "not_applicable_self_authored"
        self.assertIn("source_not_authorized", {issue.code for issue in self.issues([frame], sources=[source])})

    def test_missing_future_files_are_safe_unless_strict(self) -> None:
        with tempfile.TemporaryDirectory(dir=ROOT) as directory:
            missing_a = Path(directory) / "frames.jsonl"
            missing_b = Path(directory) / "variants.jsonl"
            with redirect_stdout(io.StringIO()) as output:
                self.assertEqual(main(["--frames", str(missing_a), "--variants", str(missing_b)]), 0)
            self.assertIn("not yet been generated", output.getvalue())
            with redirect_stderr(io.StringIO()):
                self.assertEqual(main(["--frames", str(missing_a), "--variants", str(missing_b), "--strict"]), 2)

    def test_validator_does_not_modify_benchmark_v1(self) -> None:
        v1 = ROOT / "data/rewrite_experiment/rewrite_pairs.csv"
        before = hashlib.sha256(v1.read_bytes()).hexdigest()
        self.issues()
        self.assertEqual(before, hashlib.sha256(v1.read_bytes()).hexdigest())


if __name__ == "__main__":
    unittest.main()
