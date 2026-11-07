from __future__ import annotations

import hashlib
import json
import tempfile
import unittest
from pathlib import Path

import pandas as pd

from src.build_rewrite_review_triage import QUEUE_COLUMNS, build_triage, load_pairs, triage_rows


ROOT = Path(__file__).resolve().parents[1]


def source_frame() -> pd.DataFrame:
    examples = [
        ("LOW", "Please review the notice in [URL].", "Review the notice in [URL], please."),
        ("MEDIUM", "Please review your notice.", "Please review your Acme notice."),
        ("HIGH", "Please review the notice in [URL].", "Please review it at https://evil.example/path."),
    ]
    rows = []
    for pair_id, original, rewrite in examples:
        rows.append({"pair_id": pair_id, "condition": "T0_original", "text": original, "generation_status": "original"})
        rows.append({"pair_id": pair_id, "condition": "T1_llm_neutral_rewrite", "text": rewrite, "generation_status": "completed"})
    rows.append({"pair_id": "REJECTED", "condition": "T0_original", "text": "Original", "generation_status": "original"})
    rows.append({"pair_id": "REJECTED", "condition": "T1_llm_neutral_rewrite", "text": "Unsafe", "generation_status": "rejected_safety_check"})
    return pd.DataFrame(rows)


class RewriteReviewTriageTests(unittest.TestCase):
    def test_high_medium_and_low_risk_cases(self) -> None:
        with tempfile.TemporaryDirectory(dir=ROOT) as tmp:
            path = Path(tmp) / "source.csv"
            source_frame().to_csv(path, index=False)
            queue = triage_rows(load_pairs(path)).set_index("pair_id")
        self.assertEqual(queue.loc["HIGH", "risk_level"], "high")
        self.assertTrue(queue.loc["HIGH", "newly_introduced_url"])
        self.assertFalse(queue.loc["HIGH", "defanged_url_preserved"])
        self.assertEqual(queue.loc["MEDIUM", "risk_level"], "medium")
        self.assertTrue(queue.loc["MEDIUM", "possible_entity_addition"])
        self.assertEqual(queue.loc["LOW", "risk_level"], "low")
        self.assertTrue(queue.loc["LOW", "all_safety_checks_passed"])

    def test_only_completed_rewrites_are_matched(self) -> None:
        with tempfile.TemporaryDirectory(dir=ROOT) as tmp:
            path = Path(tmp) / "source.csv"
            source_frame().to_csv(path, index=False)
            pairs = load_pairs(path)
        self.assertEqual(set(pairs["pair_id"]), {"LOW", "MEDIUM", "HIGH"})
        self.assertEqual(len(pairs), 3)

    def test_duplicate_and_equality_are_high(self) -> None:
        pairs = pd.DataFrame([
            {"pair_id": "A", "original_text": "Alpha text", "rewrite_text": "Alpha text"},
            {"pair_id": "B", "original_text": "Different text", "rewrite_text": "Alpha text"},
        ])
        queue = triage_rows(pairs).set_index("pair_id")
        self.assertTrue(queue.loc["A", "exact_match_with_original"])
        self.assertTrue(queue.loc["A", "duplicate_rewrite"])
        self.assertTrue(queue.loc["B", "duplicate_rewrite"])
        self.assertEqual(set(queue["risk_level"]), {"high"})

    def test_sentence_boundary_is_not_mistaken_for_domain(self) -> None:
        pairs = pd.DataFrame([{
            "pair_id": "BOUNDARY",
            "original_text": "Your account. Visit the official app.",
            "rewrite_text": "Visit the official app to review your account.",
        }])
        row = triage_rows(pairs).iloc[0]
        self.assertTrue(row["defanged_url_preserved"])
        self.assertFalse(row["newly_introduced_domain"])

    def test_defanged_sentence_punctuation_is_not_domain(self) -> None:
        pairs = pd.DataFrame([{
            "pair_id": "DEFANGED-BOUNDARY",
            "original_text": "Your CARD[.]Confirm details at hxxps://bank-alert[.]example[.]org",
            "rewrite_text": "Confirm your card details at hxxps://bank-alert[.]example[.]org",
        }])
        row = triage_rows(pairs).iloc[0]
        self.assertTrue(row["defanged_url_preserved"])

    def test_outputs_are_reproducible_blank_and_detector_blinded(self) -> None:
        with tempfile.TemporaryDirectory(dir=ROOT) as tmp:
            root = Path(tmp); source = root / "source.csv"
            source_frame().to_csv(source, index=False, lineterminator="\n")
            queue = root / "queue.csv"; summary_json = root / "summary.json"; summary_md = root / "summary.md"
            first = build_triage(source, queue, summary_json, summary_md)
            first_bytes = {path.name: path.read_bytes() for path in (queue, summary_json, summary_md)}
            second = build_triage(source, queue, summary_json, summary_md)
            rows = pd.read_csv(queue, keep_default_na=False)
            second_bytes = {path.name: path.read_bytes() for path in (queue, summary_json, summary_md)}
        self.assertEqual(first, second)
        self.assertEqual(first_bytes, second_bytes)
        self.assertEqual(list(rows.columns), QUEUE_COLUMNS)
        self.assertTrue(rows["human_review_decision"].eq("").all())
        self.assertTrue(rows["human_review_notes"].eq("").all())
        self.assertFalse(any("prediction" in column or "probability" in column for column in rows.columns))
        self.assertEqual(json.loads(first_bytes["summary.json"])["human_decisions_prefilled"], 0)

    def test_source_csv_is_immutable(self) -> None:
        with tempfile.TemporaryDirectory(dir=ROOT) as tmp:
            root = Path(tmp); source = root / "source.csv"
            source_frame().to_csv(source, index=False, lineterminator="\n")
            before = hashlib.sha256(source.read_bytes()).hexdigest()
            build_triage(source, root / "queue.csv", root / "summary.json", root / "summary.md")
            after = hashlib.sha256(source.read_bytes()).hexdigest()
        self.assertEqual(before, after)

    def test_missing_or_duplicate_original_fails(self) -> None:
        frame = source_frame()
        duplicate = pd.concat([frame, frame[(frame["pair_id"] == "LOW") & (frame["condition"] == "T0_original")]], ignore_index=True)
        with tempfile.TemporaryDirectory(dir=ROOT) as tmp:
            path = Path(tmp) / "source.csv"; duplicate.to_csv(path, index=False)
            with self.assertRaisesRegex(ValueError, "original pair_id"):
                load_pairs(path)


if __name__ == "__main__":
    unittest.main()
