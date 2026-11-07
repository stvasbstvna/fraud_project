from __future__ import annotations

import hashlib
import tempfile
import unittest
from pathlib import Path

import pandas as pd
from openpyxl import load_workbook

from src.export_rewrite_review_workbook import (
    CRITERION_COLUMNS,
    REVIEW_COLUMNS,
    REVIEW_SEED,
    completed_review_rows,
    export_review_workbook,
)
from src.import_rewrite_reviews import HUMAN_SOURCE_COLUMNS, import_reviews


ROOT = Path(__file__).resolve().parents[1]


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def source_row(pair_id: str, status: str, condition: str = "T1_llm_neutral_rewrite") -> dict[str, object]:
    completed = status == "completed"
    return {
        "pair_id": pair_id,
        "original_id": f"source-{pair_id}",
        "source_dataset": "SmishTank" if pair_id != "P003" else "SmishX",
        "true_label": "phishing" if pair_id != "P003" else "non_phishing",
        "binary_label": 1 if pair_id != "P003" else 0,
        "intent_type": "account_alert",
        "requested_action": "follow_link",
        "original_text": f"Original {pair_id} [URL]",
        "condition": condition,
        "text": f"Rewrite {pair_id} [URL]" if completed else "",
        "prompt_id": "neutral_rewrite_v1",
        "generator_model": "gpt-5.4-mini-2026-03-17",
        "response_id": f"response-{pair_id}" if completed else "",
        "generated_at_utc": "2026-08-27T00:00:00+00:00" if completed else "",
        "generation_status": status,
        "generation_attempts": 1,
        "rejection_reason": "rewrite equals original" if "rejected" in status else "",
        "safety_check_passed": completed,
        "human_review_status": "pending",
        "semantic_intent_preserved": "true" if completed else "pending",
        "requested_action_preserved": "true" if completed else "pending",
        "label_preserved": "true" if completed else "pending",
        "review_notes": "generator note",
    }


def sample_source() -> pd.DataFrame:
    return pd.DataFrame([
        source_row("P001", "completed"),
        source_row("P002", "completed"),
        source_row("P003", "completed"),
        source_row("P004", "rejected_safety_check"),
        source_row("P005", "pending"),
        source_row("P001", "original", "T0_original"),
    ])


def workbook_headers(sheet) -> dict[str, int]:
    return {cell.value: cell.column for cell in sheet[1]}


def fill_review_workbook(path: Path) -> None:
    workbook = load_workbook(path)
    sheet = workbook["RewriteReview"]
    headers = workbook_headers(sheet)
    decisions = {
        "P001": ("yes", "approved", ""),
        "P002": ("no", "approved", "semantic_intent_changed"),
        "P003": ("uncertain", "approved", ""),
    }
    for row_number in range(2, sheet.max_row + 1):
        pair_id = sheet.cell(row_number, headers["pair_id"]).value
        criterion_value, entered_status, reason = decisions[pair_id]
        for column in CRITERION_COLUMNS:
            sheet.cell(row_number, headers[column], criterion_value if column == CRITERION_COLUMNS[0] else "yes")
        sheet.cell(row_number, headers["human_review_status"], entered_status)
        sheet.cell(row_number, headers["rejection_reason"], reason)
        sheet.cell(row_number, headers["reviewer_id"], "reviewer-01")
        sheet.cell(row_number, headers["review_notes"], "Reviewed manually")
    workbook.save(path)


class RewriteHumanReviewTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(dir=ROOT)
        self.root = Path(self.temp.name)
        self.source_path = self.root / "rewrite_pairs.csv"
        sample_source().to_csv(self.source_path, index=False, lineterminator="\n")
        self.workbook_path = self.root / "rewrite_human_review.xlsx"

    def tearDown(self):
        self.temp.cleanup()

    def export(self) -> Path:
        return export_review_workbook(self.source_path, self.workbook_path)

    def test_exactly_completed_rows_are_exported_and_source_is_unchanged(self):
        before = digest(self.source_path)
        self.export()
        workbook = load_workbook(self.workbook_path, read_only=True)
        sheet = workbook["RewriteReview"]
        headers = workbook_headers(sheet)
        exported = [sheet.cell(row, headers["pair_id"]).value for row in range(2, sheet.max_row + 1)]
        workbook.close()
        self.assertEqual(set(exported), {"P001", "P002", "P003"})
        self.assertNotIn("P004", exported)
        self.assertNotIn("P005", exported)
        self.assertEqual(digest(self.source_path), before)

    def test_random_order_is_deterministic(self):
        source = sample_source()
        first = completed_review_rows(source, seed=REVIEW_SEED)["pair_id"].tolist()
        second = completed_review_rows(source, seed=REVIEW_SEED)["pair_id"].tolist()
        self.assertEqual(first, second)
        self.assertEqual(completed_review_rows(source)["review_order"].tolist(), [1, 2, 3])

    def test_workbook_dropdown_validations_and_sheet_order_exist(self):
        self.export()
        workbook = load_workbook(self.workbook_path)
        self.assertEqual(workbook.sheetnames[:2], ["RewriteReview", "Instructions"])
        validations = list(workbook["RewriteReview"].data_validations.dataValidation)
        formulas = {validation.formula1 for validation in validations}
        self.assertEqual(formulas, {"=CriterionOptions", "=ReviewStatusOptions", "=RejectionReasonOptions"})
        self.assertTrue(all(validation.type == "list" for validation in validations))
        workbook.close()

    def test_valid_approval_no_and_uncertain_are_enforced(self):
        self.export()
        fill_review_workbook(self.workbook_path)
        backup_dir = self.root / "backups"
        audit_dir = self.root / "audits"
        counts, backup, audit = import_reviews(
            self.source_path, self.workbook_path, backup_dir=backup_dir, audit_dir=audit_dir
        )
        self.assertEqual(counts, {"approved": 1, "rejected": 1, "needs_discussion": 1, "incomplete": 0})
        updated = pd.read_csv(self.source_path, keep_default_na=False).set_index(["pair_id", "condition"])
        self.assertEqual(updated.loc[("P001", "T1_llm_neutral_rewrite"), "human_review_status"], "approved")
        self.assertEqual(updated.loc[("P002", "T1_llm_neutral_rewrite"), "human_review_status"], "rejected")
        self.assertEqual(updated.loc[("P003", "T1_llm_neutral_rewrite"), "human_review_status"], "needs_discussion")
        self.assertTrue(backup and backup.exists())
        self.assertTrue(audit and audit.exists())

    def test_duplicate_and_unknown_pair_ids_fail(self):
        self.export()
        workbook = load_workbook(self.workbook_path)
        sheet = workbook["RewriteReview"]
        headers = workbook_headers(sheet)
        sheet.cell(3, headers["pair_id"], sheet.cell(2, headers["pair_id"]).value)
        workbook.save(self.workbook_path)
        with self.assertRaisesRegex(ValueError, "Duplicate pair IDs"):
            import_reviews(self.source_path, self.workbook_path, dry_run=True, allow_incomplete=True)

        self.export()
        workbook = load_workbook(self.workbook_path)
        sheet = workbook["RewriteReview"]
        headers = workbook_headers(sheet)
        sheet.cell(2, headers["pair_id"], "UNKNOWN")
        workbook.save(self.workbook_path)
        with self.assertRaisesRegex(ValueError, "Unknown pair IDs"):
            import_reviews(self.source_path, self.workbook_path, dry_run=True, allow_incomplete=True)

    def test_edited_original_or_rewrite_text_fails(self):
        for column in ("original_text", "rewrite_text"):
            with self.subTest(column=column):
                self.export()
                workbook = load_workbook(self.workbook_path)
                sheet = workbook["RewriteReview"]
                headers = workbook_headers(sheet)
                sheet.cell(2, headers[column], "edited")
                workbook.save(self.workbook_path)
                with self.assertRaisesRegex(ValueError, f"immutable {column} was edited"):
                    import_reviews(self.source_path, self.workbook_path, dry_run=True, allow_incomplete=True)

    def test_immutable_source_columns_remain_unchanged(self):
        before = pd.read_csv(self.source_path, keep_default_na=False)
        self.export()
        fill_review_workbook(self.workbook_path)
        import_reviews(
            self.source_path, self.workbook_path,
            backup_dir=self.root / "backups", audit_dir=self.root / "audits",
        )
        after = pd.read_csv(self.source_path, keep_default_na=False)
        immutable = [column for column in before.columns if column not in HUMAN_SOURCE_COLUMNS]
        pd.testing.assert_frame_equal(before[immutable], after[immutable], check_dtype=False)

    def test_dry_run_does_not_modify_csv_or_create_backup_or_audit(self):
        self.export()
        fill_review_workbook(self.workbook_path)
        before = digest(self.source_path)
        backup_dir = self.root / "backups"
        audit_dir = self.root / "audits"
        counts, backup, audit = import_reviews(
            self.source_path, self.workbook_path, dry_run=True,
            backup_dir=backup_dir, audit_dir=audit_dir,
        )
        self.assertEqual(counts["approved"], 1)
        self.assertIsNone(backup)
        self.assertIsNone(audit)
        self.assertEqual(digest(self.source_path), before)
        self.assertFalse(backup_dir.exists())
        self.assertFalse(audit_dir.exists())

    def test_incomplete_review_requires_flag(self):
        self.export()
        with self.assertRaisesRegex(ValueError, "required review cells are blank"):
            import_reviews(self.source_path, self.workbook_path, dry_run=True)
        counts, _, _ = import_reviews(
            self.source_path, self.workbook_path, dry_run=True, allow_incomplete=True
        )
        self.assertEqual(counts["incomplete"], 3)

    def test_rejected_safety_check_row_cannot_be_approved(self):
        self.export()
        workbook = load_workbook(self.workbook_path)
        sheet = workbook["RewriteReview"]
        headers = workbook_headers(sheet)
        rejected = sample_source().set_index("pair_id").loc["P004"]
        new_row = sheet.max_row + 1
        values = {
            "review_order": 4, "pair_id": "P004", "original_id": rejected["original_id"],
            "source_dataset": rejected["source_dataset"], "true_label": rejected["true_label"],
            "intent_type": rejected["intent_type"], "requested_action": rejected["requested_action"],
            "original_text": rejected["original_text"], "rewrite_text": rejected["text"],
            "human_review_status": "approved", "reviewer_id": "reviewer-01",
        }
        values.update({column: "yes" for column in CRITERION_COLUMNS})
        for column, value in values.items():
            sheet.cell(new_row, headers[column], value)
        workbook.save(self.workbook_path)
        with self.assertRaisesRegex(ValueError, "not completed rewrites"):
            import_reviews(self.source_path, self.workbook_path, dry_run=True)


if __name__ == "__main__":
    unittest.main()
