"""Export completed neutral rewrites to a blinded human-review workbook."""

from __future__ import annotations

import argparse
import hashlib
from pathlib import Path

import pandas as pd
from openpyxl import Workbook
from openpyxl.formatting.rule import CellIsRule
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.utils import get_column_letter
from openpyxl.worksheet.datavalidation import DataValidation
from openpyxl.workbook.defined_name import DefinedName


DEFAULT_SOURCE = Path("data/rewrite_experiment/rewrite_pairs.csv")
DEFAULT_OUTPUT = Path("data/rewrite_experiment/human_review/rewrite_human_review.xlsx")
REVIEW_SEED = 20260827
CONDITION = "T1_llm_neutral_rewrite"

CRITERION_COLUMNS = [
    "human_semantic_intent_preserved",
    "human_requested_action_preserved",
    "human_label_preserved",
    "human_entities_preserved",
    "human_no_operational_detail_added",
    "human_rewrite_is_different",
    "human_condition_fit",
]
REVIEW_COLUMNS = [
    "review_order", "pair_id", "original_id", "source_dataset", "true_label",
    "intent_type", "requested_action", "original_text", "rewrite_text",
    *CRITERION_COLUMNS,
    "human_review_status", "rejection_reason", "review_notes", "reviewer_id",
    "reviewed_at_utc",
]
CRITERION_OPTIONS = ["yes", "no", "uncertain"]
STATUS_OPTIONS = ["approved", "rejected", "needs_discussion"]
REJECTION_OPTIONS = [
    "semantic_intent_changed", "requested_action_changed", "label_changed",
    "entity_or_fact_changed", "operational_detail_added",
    "live_or_unsafe_destination", "rewrite_equals_original",
    "condition_violation", "corrupted_or_unreadable", "other",
]


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def completed_review_rows(source: pd.DataFrame, seed: int = REVIEW_SEED) -> pd.DataFrame:
    required = {
        "pair_id", "original_id", "source_dataset", "true_label", "intent_type",
        "requested_action", "original_text", "condition", "text", "generation_status",
    }
    missing = sorted(required.difference(source.columns))
    if missing:
        raise ValueError(f"rewrite_pairs.csv is missing columns: {missing}")
    selected = source[
        source["condition"].eq(CONDITION)
        & source["generation_status"].eq("completed")
    ].copy()
    if selected.empty:
        raise ValueError("No completed T1 rewrites are available for human review")
    if selected["pair_id"].astype(str).str.strip().eq("").any() or selected["pair_id"].duplicated().any():
        raise ValueError("Completed rewrite pair_id values must be non-empty and unique")
    selected = selected.sample(frac=1, random_state=seed).reset_index(drop=True)
    output = pd.DataFrame({
        "review_order": range(1, len(selected) + 1),
        "pair_id": selected["pair_id"].astype(str),
        "original_id": selected["original_id"].astype(str),
        "source_dataset": selected["source_dataset"].astype(str),
        "true_label": selected["true_label"].astype(str),
        "intent_type": selected["intent_type"].astype(str),
        "requested_action": selected["requested_action"].astype(str),
        "original_text": selected["original_text"].astype(str),
        "rewrite_text": selected["text"].astype(str),
    })
    for column in CRITERION_COLUMNS:
        output[column] = selected[column].astype(str) if column in selected else ""
        output.loc[~output[column].isin(CRITERION_OPTIONS), column] = ""
    source_status = selected.get("human_review_status", pd.Series("", index=selected.index)).astype(str)
    output["human_review_status"] = source_status.where(source_status.isin(STATUS_OPTIONS), "")
    source_reason = selected.get("human_rejection_reason", pd.Series("", index=selected.index)).astype(str)
    output["rejection_reason"] = source_reason.where(source_reason.isin(REJECTION_OPTIONS), "")
    output["review_notes"] = selected.get("human_review_notes", pd.Series("", index=selected.index)).astype(str)
    output["reviewer_id"] = selected.get("reviewer_id", pd.Series("", index=selected.index)).astype(str)
    output["reviewed_at_utc"] = selected.get("reviewed_at_utc", pd.Series("", index=selected.index)).astype(str)
    return output[REVIEW_COLUMNS]


def _add_named_list(workbook: Workbook, name: str, sheet: str, column: str, values: list[str]) -> None:
    reference = f"'{sheet}'!${column}$2:${column}${len(values) + 1}"
    workbook.defined_names.add(DefinedName(name, attr_text=reference))


def _instructions_sheet(workbook: Workbook) -> None:
    sheet = workbook.create_sheet("Instructions")
    sheet.sheet_view.showGridLines = False
    rows = [
        ("Human Review Rubric", "Banking-smishing neutral LLM rewrite experiment"),
        ("Purpose", "Judge semantic and safety fidelity only. Do not use detector predictions, probabilities, errors, or dashboard results."),
        ("Blinding", "Review each original and rewrite side by side using pair_id. The randomized order is deterministic."),
        ("Randomization seed", str(REVIEW_SEED)),
        ("Eligible rows", "Only condition=T1_llm_neutral_rewrite and generation_status=completed are exported."),
        ("Criterion values", "yes = requirement satisfied; no = requirement violated; uncertain = reviewer cannot decide confidently."),
        ("Semantic intent", "yes only when the same high-level situation and communicative intent are preserved."),
        ("Requested action", "yes only when the requested-action category is unchanged; no new action may be introduced."),
        ("Label", "yes only when phishing remains phishing and legitimate remains legitimate."),
        ("Entities and facts", "yes only when brands, services, amounts, dates, account context, and other material facts are preserved without invention."),
        ("Operational detail", "yes only when no new link, domain, phone number, email, credential, personal datum, payment instruction, or usable destination was added."),
        ("Rewrite differs", "yes only when rewrite_text is meaningfully different from original_text; cosmetic whitespace alone is insufficient."),
        ("Condition fit", "yes only when the output is one neutral rewrite, stays defanged, and does not add urgency, threat, reward, persuasion, or detector-targeting behavior."),
        ("Approval rule", "approved only when every required criterion is yes."),
        ("Rejection rule", "rejected when any required criterion is no; select the best rejection_reason."),
        ("Discussion rule", "needs_discussion when no criterion is no and at least one criterion is uncertain."),
        ("Required fields", "Complete all seven criteria, human_review_status, and reviewer_id. A rejected row also requires rejection_reason."),
        ("Notes", "Use review_notes for concise evidence, ambiguity, or rationale. Do not edit immutable source fields."),
        ("Import", "The importer recomputes status from criteria, rejects edited source values, timestamps the decision, backs up the CSV, and writes an audit file."),
    ]
    for row_number, (label, description) in enumerate(rows, start=1):
        sheet.cell(row_number, 1, label)
        sheet.cell(row_number, 2, description)
    sheet["A1"].font = Font(name="Aptos Display", size=18, bold=True, color="FFFFFF")
    sheet["B1"].font = Font(name="Aptos", size=12, bold=True, color="FFFFFF")
    for cell in sheet[1]:
        cell.fill = PatternFill("solid", fgColor="1F4E78")
    for row_number in range(2, len(rows) + 1):
        sheet.cell(row_number, 1).font = Font(name="Aptos", bold=True, color="1F2937")
        sheet.cell(row_number, 1).fill = PatternFill("solid", fgColor="EAF2F8")
        sheet.cell(row_number, 2).alignment = Alignment(wrap_text=True, vertical="top")
        sheet.row_dimensions[row_number].height = 34
    sheet.column_dimensions["A"].width = 24
    sheet.column_dimensions["B"].width = 105
    sheet.freeze_panes = "A2"

    for index, value in enumerate(CRITERION_OPTIONS, start=2):
        sheet.cell(index, 4, value)
    for index, value in enumerate(STATUS_OPTIONS, start=2):
        sheet.cell(index, 5, value)
    for index, value in enumerate(REJECTION_OPTIONS, start=2):
        sheet.cell(index, 6, value)
    for column in ("D", "E", "F"):
        sheet.column_dimensions[column].hidden = True


def create_workbook(review: pd.DataFrame, output_path: Path) -> Path:
    workbook = Workbook()
    sheet = workbook.active
    sheet.title = "RewriteReview"
    sheet.sheet_view.showGridLines = False
    _instructions_sheet(workbook)
    _add_named_list(workbook, "CriterionOptions", "Instructions", "D", CRITERION_OPTIONS)
    _add_named_list(workbook, "ReviewStatusOptions", "Instructions", "E", STATUS_OPTIONS)
    _add_named_list(workbook, "RejectionReasonOptions", "Instructions", "F", REJECTION_OPTIONS)

    for column_index, name in enumerate(REVIEW_COLUMNS, start=1):
        sheet.cell(1, column_index, name)
    for row_index, row in enumerate(review.itertuples(index=False, name=None), start=2):
        for column_index, value in enumerate(row, start=1):
            sheet.cell(row_index, column_index, value)

    header_fill = PatternFill("solid", fgColor="1F4E78")
    header_font = Font(name="Aptos", color="FFFFFF", bold=True)
    thin_gray = Side(style="thin", color="D9E2F3")
    for cell in sheet[1]:
        cell.fill = header_fill
        cell.font = header_font
        cell.alignment = Alignment(wrap_text=True, horizontal="center", vertical="center")
        cell.border = Border(bottom=Side(style="medium", color="9FBAD0"))
    sheet.row_dimensions[1].height = 42
    sheet.freeze_panes = "H2"
    sheet.auto_filter.ref = f"A1:{get_column_letter(len(REVIEW_COLUMNS))}{len(review) + 1}"

    widths = {
        "review_order": 12, "pair_id": 15, "original_id": 24, "source_dataset": 14,
        "true_label": 14, "intent_type": 19, "requested_action": 20,
        "original_text": 62, "rewrite_text": 62, "human_review_status": 20,
        "rejection_reason": 28, "review_notes": 38, "reviewer_id": 18,
        "reviewed_at_utc": 24,
    }
    for index, name in enumerate(REVIEW_COLUMNS, start=1):
        sheet.column_dimensions[get_column_letter(index)].width = widths.get(name, 23)
    for row_number in range(2, len(review) + 2):
        sheet.row_dimensions[row_number].height = 72
        for cell in sheet[row_number]:
            cell.alignment = Alignment(wrap_text=True, vertical="top")
            cell.border = Border(bottom=thin_gray)
    for column in CRITERION_COLUMNS + ["human_review_status", "rejection_reason"]:
        column_index = REVIEW_COLUMNS.index(column) + 1
        for row_number in range(2, len(review) + 2):
            sheet.cell(row_number, column_index).alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)

    criterion_validation = DataValidation(type="list", formula1="=CriterionOptions", allow_blank=True)
    status_validation = DataValidation(type="list", formula1="=ReviewStatusOptions", allow_blank=True)
    reason_validation = DataValidation(type="list", formula1="=RejectionReasonOptions", allow_blank=True)
    for validation in (criterion_validation, status_validation, reason_validation):
        validation.error = "Choose a value from the dropdown list."
        validation.errorTitle = "Invalid review value"
        validation.showErrorMessage = True
        sheet.add_data_validation(validation)
    last_row = len(review) + 1
    for column in CRITERION_COLUMNS:
        letter = get_column_letter(REVIEW_COLUMNS.index(column) + 1)
        criterion_validation.add(f"{letter}2:{letter}{last_row}")
    status_letter = get_column_letter(REVIEW_COLUMNS.index("human_review_status") + 1)
    reason_letter = get_column_letter(REVIEW_COLUMNS.index("rejection_reason") + 1)
    status_validation.add(f"{status_letter}2:{status_letter}{last_row}")
    reason_validation.add(f"{reason_letter}2:{reason_letter}{last_row}")

    green = PatternFill("solid", fgColor="C6EFCE")
    red = PatternFill("solid", fgColor="FFC7CE")
    amber = PatternFill("solid", fgColor="FFEB9C")
    for column in CRITERION_COLUMNS:
        letter = get_column_letter(REVIEW_COLUMNS.index(column) + 1)
        cell_range = f"{letter}2:{letter}{last_row}"
        sheet.conditional_formatting.add(cell_range, CellIsRule(operator="equal", formula=['"yes"'], fill=green))
        sheet.conditional_formatting.add(cell_range, CellIsRule(operator="equal", formula=['"no"'], fill=red))
        sheet.conditional_formatting.add(cell_range, CellIsRule(operator="equal", formula=['"uncertain"'], fill=amber))
    status_range = f"{status_letter}2:{status_letter}{last_row}"
    sheet.conditional_formatting.add(status_range, CellIsRule(operator="equal", formula=['"approved"'], fill=green))
    sheet.conditional_formatting.add(status_range, CellIsRule(operator="equal", formula=['"rejected"'], fill=red))
    sheet.conditional_formatting.add(status_range, CellIsRule(operator="equal", formula=['"needs_discussion"'], fill=amber))

    sheet.sheet_properties.pageSetUpPr.fitToPage = True
    sheet.page_setup.fitToWidth = 1
    sheet.page_setup.fitToHeight = 0
    sheet.auto_filter.ref = f"A1:{get_column_letter(len(REVIEW_COLUMNS))}{last_row}"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    workbook.save(output_path)
    return output_path


def export_review_workbook(source_path: Path, output_path: Path, seed: int = REVIEW_SEED) -> Path:
    before = sha256(source_path)
    source = pd.read_csv(source_path, keep_default_na=False)
    review = completed_review_rows(source, seed=seed)
    result = create_workbook(review, output_path)
    if sha256(source_path) != before:
        raise RuntimeError("Export modified rewrite_pairs.csv")
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, default=DEFAULT_SOURCE)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--seed", type=int, default=REVIEW_SEED)
    args = parser.parse_args()
    output = export_review_workbook(args.source, args.output, seed=args.seed)
    rows = completed_review_rows(pd.read_csv(args.source, keep_default_na=False), seed=args.seed)
    print(f"Exported completed rewrites: {len(rows)}")
    print(f"Randomization seed: {args.seed}")
    print(f"Workbook: {output}")


if __name__ == "__main__":
    main()
