from __future__ import annotations

import hashlib
import tempfile
import unittest
from pathlib import Path

import pandas as pd

from src.import_rewrite_reviews import import_reviews
from src.review_rewrites_app import (
    CRITERION_COLUMNS,
    automated_checks,
    deterministic_review_order,
    load_completed_rewrites,
    load_or_create_decisions,
    save_human_decision,
)


def fixture_rows() -> pd.DataFrame:
    common = {
        "source_dataset": "fixture", "binary_label": 1,
        "generator_model": "frozen", "generation_attempts": 1,
    }
    return pd.DataFrame([
        {**common, "pair_id": "P1", "original_id": "O1", "true_label": "phishing", "intent_type": "alert", "requested_action": "call", "original_text": "Call [PHONE] about $50 case 123", "condition": "T1_llm_neutral_rewrite", "text": "Regarding case 123 and $50, call [PHONE].", "generation_status": "completed"},
        {**common, "pair_id": "P2", "original_id": "O2", "true_label": "legitimate", "intent_type": "notice", "requested_action": "none", "original_text": "Payment of $20 posted", "condition": "T1_llm_neutral_rewrite", "text": "Your $20 payment has posted.", "generation_status": "completed"},
        {**common, "pair_id": "P3", "original_id": "O3", "true_label": "phishing", "intent_type": "alert", "requested_action": "visit", "original_text": "Visit [URL]", "condition": "T1_llm_neutral_rewrite", "text": "", "generation_status": "rejected_safety_check"},
        {**common, "pair_id": "P4", "original_id": "O4", "true_label": "phishing", "intent_type": "alert", "requested_action": "call", "original_text": "Call [PHONE]", "condition": "T1_llm_neutral_rewrite", "text": "", "generation_status": "pending"},
        {**common, "pair_id": "P1", "original_id": "O1", "true_label": "phishing", "intent_type": "alert", "requested_action": "call", "original_text": "Call [PHONE] about $50 case 123", "condition": "T0_original", "text": "Call [PHONE] about $50 case 123", "generation_status": "original"},
    ])


class ReviewRewritesAppTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory(dir=Path.cwd())
        self.root = Path(self.temp.name)
        self.source = self.root / "rewrite_pairs.csv"
        fixture_rows().to_csv(self.source, index=False)
        self.decisions_path = self.root / "review_decisions.csv"

    def tearDown(self) -> None:
        self.temp.cleanup()

    @staticmethod
    def digest(path: Path) -> str:
        return hashlib.sha256(path.read_bytes()).hexdigest()

    def test_completed_rows_only_and_source_never_changes(self) -> None:
        before = self.digest(self.source)
        rows = load_completed_rewrites(self.source)
        decisions = load_or_create_decisions(rows, self.decisions_path)
        self.assertEqual(set(rows["pair_id"]), {"P1", "P2"})
        self.assertEqual(len(decisions), 2)
        self.assertEqual(before, self.digest(self.source))

    def test_deterministic_order_is_stable(self) -> None:
        rows = load_completed_rewrites(self.source)
        first = deterministic_review_order(rows)
        second = deterministic_review_order(rows.sample(frac=1, random_state=99))
        # The source order is frozen in the real CSV; repeated runs on it are stable.
        self.assertEqual(first["pair_id"].tolist(), deterministic_review_order(rows)["pair_id"].tolist())
        self.assertEqual(sorted(second["pair_id"]), sorted(first["pair_id"]))

    def test_automated_checks_flag_unchanged_placeholder_url_number_and_amount(self) -> None:
        unchanged = automated_checks("Call [PHONE]", "Call [PHONE]", "call")
        self.assertFalse(unchanged["rewrite_differs"])
        self.assertEqual(unchanged["risk_level"], "red")
        missing = automated_checks("Call [PHONE]", "Call support", "call")
        self.assertFalse(missing["placeholders_preserved"])
        live = automated_checks("Visit [URL]", "Visit https://evil.example", "visit")
        self.assertFalse(live["no_new_live_url"])
        changed = automated_checks("Pay $50 using code 123", "Pay $70 using code 999", "pay")
        self.assertTrue(changed["changed_numeric_tokens"])
        self.assertTrue(changed["changed_amounts"])

    def test_decision_persists_resume_and_requires_explicit_action(self) -> None:
        rows = load_completed_rewrites(self.source)
        decisions = load_or_create_decisions(rows, self.decisions_path)
        self.assertTrue(decisions["human_review_status"].eq("").all())
        decisions = save_human_decision(decisions, "P1", "approved", reviewer_id="R1", decisions_path=self.decisions_path)
        resumed = load_or_create_decisions(rows, self.decisions_path)
        row = resumed.set_index("pair_id").loc["P1"]
        self.assertEqual(row["human_review_status"], "approved")
        self.assertTrue(all(row[column] == "yes" for column in CRITERION_COLUMNS))

    def test_reject_requires_reason_and_no_criterion(self) -> None:
        decisions = load_or_create_decisions(load_completed_rewrites(self.source), self.decisions_path)
        criteria = {column: "yes" for column in CRITERION_COLUMNS}
        with self.assertRaisesRegex(ValueError, "reason"):
            save_human_decision(decisions, "P1", "rejected", reviewer_id="R", criteria=criteria, decisions_path=self.decisions_path)
        with self.assertRaisesRegex(ValueError, "criterion"):
            save_human_decision(decisions, "P1", "rejected", reviewer_id="R", criteria=criteria, rejection_reason="other", decisions_path=self.decisions_path)

    def test_csv_dry_run_and_import_preserve_immutable_data(self) -> None:
        rows = load_completed_rewrites(self.source)
        decisions = load_or_create_decisions(rows, self.decisions_path)
        decisions = save_human_decision(decisions, "P1", "approved", reviewer_id="R", decisions_path=self.decisions_path)
        criteria = {column: "yes" for column in CRITERION_COLUMNS}
        criteria["human_condition_fit"] = "no"
        save_human_decision(decisions, "P2", "rejected", reviewer_id="R", criteria=criteria, rejection_reason="condition_violation", decisions_path=self.decisions_path)
        before_bytes = self.source.read_bytes()
        counts, backup, audit = import_reviews(self.source, self.decisions_path, dry_run=True)
        self.assertEqual(counts["approved"], 1)
        self.assertEqual(self.source.read_bytes(), before_bytes)
        self.assertIsNone(backup)
        immutable_before = pd.read_csv(self.source, keep_default_na=False)
        counts, backup, audit = import_reviews(self.source, self.decisions_path, backup_dir=self.root / "backups", audit_dir=self.root / "audits")
        immutable_after = pd.read_csv(self.source, keep_default_na=False)
        excluded = set(CRITERION_COLUMNS) | {"human_review_status", "human_rejection_reason", "human_review_notes", "reviewer_id", "reviewed_at_utc"}
        columns = [column for column in immutable_before.columns if column not in excluded]
        pd.testing.assert_frame_equal(immutable_before[columns], immutable_after[columns])
        self.assertTrue(backup.exists())
        self.assertTrue(audit.exists())

    def test_unknown_and_duplicate_pair_ids_fail(self) -> None:
        decisions = load_or_create_decisions(load_completed_rewrites(self.source), self.decisions_path)
        duplicate = pd.concat([decisions, decisions.iloc[[0]]], ignore_index=True)
        duplicate.to_csv(self.decisions_path, index=False)
        with self.assertRaisesRegex(ValueError, "Duplicate"):
            import_reviews(self.source, self.decisions_path, allow_incomplete=True, dry_run=True)
        unknown = decisions.copy()
        unknown.loc[0, "pair_id"] = "UNKNOWN"
        unknown.to_csv(self.decisions_path, index=False)
        with self.assertRaisesRegex(ValueError, "Unknown"):
            import_reviews(self.source, self.decisions_path, allow_incomplete=True, dry_run=True)


if __name__ == "__main__":
    unittest.main()
