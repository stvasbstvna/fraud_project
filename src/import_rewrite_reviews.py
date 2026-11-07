"""Validate and atomically import human rewrite-review decisions."""

from __future__ import annotations

import argparse
import os
import shutil
import tempfile
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd
from openpyxl import load_workbook

try:
    from src.export_rewrite_review_workbook import REVIEW_COLUMNS
    from src.review_rewrites_app import (
        CONDITION, CRITERION_COLUMNS, DECISION_COLUMNS, REJECTION_REASONS,
        text_sha256,
    )
except ModuleNotFoundError:  # Support direct script execution.
    from export_rewrite_review_workbook import REVIEW_COLUMNS
    from review_rewrites_app import (
        CONDITION, CRITERION_COLUMNS, DECISION_COLUMNS, REJECTION_REASONS,
        text_sha256,
    )

DEFAULT_SOURCE = Path("data/rewrite_experiment/rewrite_pairs.csv")
DEFAULT_BACKUP_DIR = Path("data/rewrite_experiment/human_review/backups")
DEFAULT_AUDIT_DIR = Path("results/rewrite_experiment/human_review")
IMMUTABLE_WORKBOOK_TO_SOURCE = {
    "original_id": "original_id", "source_dataset": "source_dataset",
    "true_label": "true_label", "intent_type": "intent_type",
    "requested_action": "requested_action", "original_text": "original_text",
    "rewrite_text": "text",
}
HUMAN_SOURCE_COLUMNS = [
    *CRITERION_COLUMNS, "human_review_status", "human_rejection_reason",
    "human_review_notes", "reviewer_id", "reviewed_at_utc",
]


def utc_stamp() -> tuple[str, str]:
    now = datetime.now(timezone.utc)
    return now.strftime("%Y%m%dT%H%M%S%fZ"), now.isoformat()


def load_review_file(review_file: Path) -> pd.DataFrame:
    if review_file.suffix.casefold() == ".csv":
        review = pd.read_csv(review_file, keep_default_na=False)
        missing = sorted(set(DECISION_COLUMNS).difference(review.columns))
        if missing:
            raise ValueError(f"Review CSV is missing columns: {missing}")
        return review[DECISION_COLUMNS].copy()
    if review_file.suffix.casefold() != ".xlsx":
        raise ValueError("--review-file must be a .csv or .xlsx file")
    workbook = load_workbook(review_file, read_only=True, data_only=True)
    if "RewriteReview" not in workbook.sheetnames:
        workbook.close()
        raise ValueError("Review workbook is missing the RewriteReview worksheet")
    sheet = workbook["RewriteReview"]
    values = list(sheet.iter_rows(values_only=True))
    workbook.close()
    if not values:
        raise ValueError("RewriteReview worksheet is empty")
    headers = [str(value).strip() if value is not None else "" for value in values[0]]
    missing = sorted(set(REVIEW_COLUMNS).difference(headers))
    if missing:
        raise ValueError(f"Review workbook is missing columns: {missing}")
    records = []
    for values_row in values[1:]:
        row = {name: "" if value is None else str(value) for name, value in zip(headers, values_row) if name}
        if row.get("pair_id", "").strip():
            records.append(row)
    return pd.DataFrame(records, columns=headers)


load_review_sheet = load_review_file  # Backward compatibility for workbook tests.


def _derive_decision(row: pd.Series, allow_incomplete: bool) -> tuple[str, list[str]]:
    criteria = {column: str(row.get(column, "")).strip().lower() for column in CRITERION_COLUMNS}
    invalid = [f"{column}={value!r}" for column, value in criteria.items() if value and value not in {"yes", "no", "uncertain"}]
    if invalid:
        raise ValueError("invalid criterion values: " + ", ".join(invalid))
    entered = str(row.get("human_review_status", "")).strip().lower()
    if entered == "needs_discussion":
        entered = "uncertain"
    if entered and entered not in {"approved", "rejected", "uncertain"}:
        raise ValueError(f"invalid human_review_status {entered!r}")
    reason = str(row.get("rejection_reason", "")).strip().lower()
    if reason and reason not in REJECTION_REASONS:
        raise ValueError(f"invalid rejection_reason {reason!r}")
    missing = [column for column, value in criteria.items() if not value]
    if not entered:
        missing.append("human_review_status")
    if not str(row.get("reviewer_id", "")).strip():
        missing.append("reviewer_id")
    if missing:
        if allow_incomplete:
            return "incomplete", missing
        raise ValueError(f"required review cells are blank: {missing}")
    values = set(criteria.values())
    enforced = "rejected" if "no" in values else "needs_discussion" if "uncertain" in values else "approved"
    if enforced == "rejected" and not reason:
        if allow_incomplete:
            return "incomplete", ["rejection_reason"]
        raise ValueError("rejection_reason is required when any criterion is no")
    return enforced, []


def validate_reviews(source: pd.DataFrame, review: pd.DataFrame, *, allow_incomplete: bool = False) -> tuple[pd.DataFrame, pd.DataFrame]:
    if review.empty or "pair_id" not in review:
        raise ValueError("Review file contains no rows or is missing pair_id")
    pair_ids = review["pair_id"].astype(str).str.strip()
    duplicates = sorted(pair_ids[pair_ids.duplicated(keep=False)].unique())
    if duplicates:
        raise ValueError(f"Duplicate pair IDs in review file: {duplicates}")
    rewrites = source[source["condition"].eq(CONDITION)].copy()
    if rewrites["pair_id"].duplicated().any():
        raise ValueError("Source CSV contains duplicate T1 pair IDs")
    rewrites.index = rewrites["pair_id"].astype(str)
    unknown = sorted(set(pair_ids).difference(rewrites.index))
    if unknown:
        raise ValueError(f"Unknown pair IDs in review file: {unknown}")
    non_completed = sorted(pair_id for pair_id in pair_ids if str(rewrites.loc[pair_id, "generation_status"]) != "completed")
    if non_completed:
        raise ValueError(f"Review file includes rows that are not completed rewrites: {non_completed}")
    eligible_ids = set(rewrites.loc[rewrites["generation_status"].eq("completed"), "pair_id"].astype(str))
    missing_ids = sorted(eligible_ids.difference(pair_ids))
    if missing_ids and not allow_incomplete:
        raise ValueError(f"Review file is missing completed pair IDs: {missing_ids}")

    updated = source.copy()
    for column in HUMAN_SOURCE_COLUMNS:
        if column not in updated:
            updated[column] = ""
    token, reviewed_at = utc_stamp()
    audit_rows: list[dict[str, object]] = []
    is_hash_file = {"original_text_sha256", "rewrite_text_sha256"}.issubset(review.columns)
    for _, review_row in review.iterrows():
        pair_id = str(review_row["pair_id"]).strip()
        source_row = rewrites.loc[pair_id]
        if is_hash_file:
            if str(review_row["original_text_sha256"]) != text_sha256(source_row["original_text"]):
                raise ValueError(f"{pair_id}: original text hash does not match source")
            if str(review_row["rewrite_text_sha256"]) != text_sha256(source_row["text"]):
                raise ValueError(f"{pair_id}: rewrite text hash does not match source")
            if str(review_row.get("original_id", "")) != str(source_row["original_id"]):
                raise ValueError(f"{pair_id}: immutable original_id was edited")
        else:
            for review_column, source_column in IMMUTABLE_WORKBOOK_TO_SOURCE.items():
                if str(review_row.get(review_column, "")) != str(source_row[source_column]):
                    raise ValueError(f"{pair_id}: immutable {review_column} was edited")
        try:
            enforced, incomplete_fields = _derive_decision(review_row, allow_incomplete)
        except ValueError as error:
            raise ValueError(f"{pair_id}: {error}") from error
        indices = updated.index[updated["pair_id"].astype(str).eq(pair_id) & updated["condition"].eq(CONDITION)]
        if len(indices) != 1:
            raise ValueError(f"{pair_id}: source row must exist exactly once")
        index = indices[0]
        for column in CRITERION_COLUMNS:
            updated.at[index, column] = str(review_row.get(column, "")).strip().lower()
        updated.at[index, "human_review_status"] = enforced
        updated.at[index, "human_rejection_reason"] = str(review_row.get("rejection_reason", "")).strip().lower()
        updated.at[index, "human_review_notes"] = str(review_row.get("review_notes", "")).strip()
        updated.at[index, "reviewer_id"] = str(review_row.get("reviewer_id", "")).strip()
        updated.at[index, "reviewed_at_utc"] = reviewed_at if enforced != "incomplete" else ""
        audit_rows.append({
            "imported_at_utc": reviewed_at, "pair_id": pair_id,
            "original_id": str(source_row["original_id"]),
            "entered_human_review_status": str(review_row.get("human_review_status", "")).strip().lower(),
            "enforced_human_review_status": enforced,
            "human_rejection_reason": str(review_row.get("rejection_reason", "")).strip().lower(),
            "reviewer_id": str(review_row.get("reviewer_id", "")).strip(),
            "incomplete_fields": "|".join(incomplete_fields),
            **{column: str(review_row.get(column, "")).strip().lower() for column in CRITERION_COLUMNS},
            "human_review_notes": str(review_row.get("review_notes", "")).strip(),
            "original_text_sha256": text_sha256(source_row["original_text"]),
            "rewrite_text_sha256": text_sha256(source_row["text"]),
        })
    audit = pd.DataFrame(audit_rows)
    audit.attrs["timestamp_token"] = token
    return updated, audit


def decision_counts(audit: pd.DataFrame) -> dict[str, int]:
    status = audit.get("enforced_human_review_status", pd.Series(dtype=str))
    uncertain = int(status.eq("needs_discussion").sum())
    return {
        "approved": int(status.eq("approved").sum()),
        "rejected": int(status.eq("rejected").sum()),
        "needs_discussion": uncertain,
        "incomplete": int(status.eq("incomplete").sum()),
    }


def import_reviews(source_path: Path, review_file: Path, *, allow_incomplete: bool = False, dry_run: bool = False, backup_dir: Path = DEFAULT_BACKUP_DIR, audit_dir: Path = DEFAULT_AUDIT_DIR) -> tuple[dict[str, int], Path | None, Path | None]:
    source = pd.read_csv(source_path, keep_default_na=False)
    updated, audit = validate_reviews(source, load_review_file(review_file), allow_incomplete=allow_incomplete)
    counts = decision_counts(audit)
    if dry_run:
        return counts, None, None
    token = str(audit.attrs["timestamp_token"])
    backup_dir.mkdir(parents=True, exist_ok=True)
    audit_dir.mkdir(parents=True, exist_ok=True)
    backup_path = backup_dir / f"rewrite_pairs_before_review_import_{token}.csv"
    audit_path = audit_dir / f"human_review_import_audit_{token}.csv"
    shutil.copy2(source_path, backup_path)
    descriptor, temp_name = tempfile.mkstemp(prefix="rewrite_pairs_review_", suffix=".tmp", dir=source_path.parent)
    os.close(descriptor)
    temp_path = Path(temp_name)
    try:
        updated.to_csv(temp_path, index=False, lineterminator="\n")
        audit.to_csv(audit_path, index=False, lineterminator="\n")
        os.replace(temp_path, source_path)
    finally:
        if temp_path.exists():
            temp_path.unlink()
    return counts, backup_path, audit_path


def _print_counts(counts: dict[str, int]) -> None:
    print(f"Review counts: approved={counts['approved']}, rejected={counts['rejected']}, uncertain={counts['needs_discussion']}, incomplete={counts['incomplete']}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--review-file", type=Path, required=True)
    parser.add_argument("--source", type=Path, default=DEFAULT_SOURCE)
    parser.add_argument("--allow-incomplete", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--backup-dir", type=Path, default=DEFAULT_BACKUP_DIR)
    parser.add_argument("--audit-dir", type=Path, default=DEFAULT_AUDIT_DIR)
    args = parser.parse_args()
    counts, backup, audit = import_reviews(args.source, args.review_file, allow_incomplete=args.allow_incomplete, dry_run=args.dry_run, backup_dir=args.backup_dir, audit_dir=args.audit_dir)
    _print_counts(counts)
    if args.dry_run:
        print("Dry run: source CSV was not modified; no backup or audit file was written.")
    else:
        print(f"Backup: {backup}")
        print(f"Audit: {audit}")
        print(f"Updated atomically: {args.source}")


if __name__ == "__main__":
    main()
