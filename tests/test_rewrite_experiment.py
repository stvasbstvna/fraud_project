import unittest
from pathlib import Path

import pandas as pd

from src.generate_llm_rewrites_openai import local_safety_check
from src.prepare_rewrite_experiment import build_pairs, sha256, validate_no_training_overlap


ROOT = Path(__file__).resolve().parents[1]


class RewriteExperimentTests(unittest.TestCase):
    def test_safety_check_rejects_live_url(self):
        parsed = {
            "semantic_intent_preserved": True,
            "requested_action_preserved": True,
            "label_preserved": True,
            "operational_detail_added": False,
        }
        safe, note = local_safety_check("Use [URL]", "Use https://example.com and [URL]", parsed)
        self.assertFalse(safe)
        self.assertIn("live URL", note)

    def test_safety_check_preserves_ids_placeholders_and_defanged_url(self):
        parsed = {
            "pair_id": "BRW-0001",
            "original_id": "source-1",
            "semantic_intent_preserved": True,
            "requested_action_preserved": True,
            "label_preserved": True,
            "operational_detail_added": False,
        }
        original = "Use [BANK] at hxxps://safe[.]invalid/path and [PHONE]."
        rewrite = "Contact [BANK] through hxxps://safe[.]invalid/path using [PHONE]."
        safe, note = local_safety_check(
            original, rewrite, parsed,
            expected_pair_id="BRW-0001", expected_original_id="source-1",
        )
        self.assertTrue(safe, note)
        parsed["pair_id"] = "changed"
        safe, note = local_safety_check(
            original, rewrite, parsed,
            expected_pair_id="BRW-0001", expected_original_id="source-1",
        )
        self.assertFalse(safe)
        self.assertIn("pair_id changed", note)

    def test_build_pairs_requires_frozen_size(self):
        frame = pd.DataFrame([{
            "id": "x", "text": "safe", "binary_label": 0,
            "class_label": "non_phishing", "source_dataset": "test",
            "intent_type": "other", "requested_action": "none",
            "split": "banking_test",
        }])
        with self.assertRaisesRegex(ValueError, "Expected 156"):
            build_pairs(frame)

    def test_frozen_pair_counts_and_conditions(self):
        frozen = pd.read_csv(ROOT / "data/rewrite_experiment/original_banking_test_frozen.csv")
        pairs = build_pairs(frozen)
        self.assertEqual(len(pairs), 312)
        self.assertEqual(pairs["pair_id"].nunique(), 156)
        self.assertEqual(
            pairs["condition"].value_counts().to_dict(),
            {"T0_original": 156, "T1_llm_neutral_rewrite": 156},
        )
        originals = pairs[pairs["condition"].eq("T0_original")]
        self.assertEqual(originals["binary_label"].value_counts().to_dict(), {1: 146, 0: 10})
        self.assertTrue(pairs.groupby(["pair_id", "condition"]).size().eq(1).all())

    def test_frozen_test_has_no_training_overlap(self):
        frozen = pd.read_csv(ROOT / "data/rewrite_experiment/original_banking_test_frozen.csv")
        train = pd.read_csv(ROOT / "data/final/train_sms.csv")
        validate_no_training_overlap(frozen, train)

    def test_two_frozen_model_hashes_match(self):
        hashes = pd.read_csv(ROOT / "results/rewrite_experiment/model_hashes.csv")
        self.assertEqual(len(hashes), 2)
        for row in hashes.itertuples(index=False):
            model_path = ROOT / Path(str(row.model_file))
            self.assertTrue(model_path.exists())
            self.assertEqual(sha256(model_path), row.sha256)

    def test_evaluator_never_calls_fit(self):
        source = (ROOT / "src/evaluate_rewrite_robustness.py").read_text(encoding="utf-8")
        self.assertNotIn(".fit(", source)


if __name__ == "__main__":
    unittest.main()
