"""Build a deterministic, detector-blinded Benchmark v2 pilot review sample."""

from __future__ import annotations

import argparse
import csv
import hashlib
import itertools
import json
from pathlib import Path

from openpyxl import Workbook
from openpyxl.formatting.rule import CellIsRule
from openpyxl.styles import Alignment, Font, PatternFill
from openpyxl.utils import get_column_letter
from openpyxl.worksheet.datavalidation import DataValidation


DEFAULT_PILOT_DIR = Path("data/benchmark_v2/pilot")
SELECTION_SEED = 20260827
CONDITIONS = ("C0", "C1", "C2", "C3")
REVIEW_FIELDS = (
    "semantic_intent_preserved", "requested_action_preserved", "label_preserved",
    "entities_placeholders_preserved", "no_operational_detail_added",
    "rewrite_is_different", "condition_fit", "action_explicitness_1_to_5",
    "decision", "rejection_reason", "review_notes", "reviewer_id",
)


def read_jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def _tie_key(seed: int, scenario_ids: tuple[str, ...]) -> str:
    return hashlib.sha256(f"{seed}|{'|'.join(scenario_ids)}".encode()).hexdigest()


def select_scenarios(frames: list[dict], seed: int = SELECTION_SEED) -> list[str]:
    """Select 3 scenarios/population, maximizing family and style diversity."""
    selected: list[str] = []
    for population in ("phishing", "legitimate"):
        candidates = sorted((row for row in frames if row["population"] == population), key=lambda x: x["scenario_id"])
        choices = []
        for combo in itertools.combinations(candidates, 3):
            ids = tuple(row["scenario_id"] for row in combo)
            score = (len({row["scenario_family"] for row in combo}), len({row["style_slot"] for row in combo}))
            choices.append((-score[0], -score[1], _tie_key(seed, ids), ids))
        selected.extend(min(choices)[3])
    return selected


def build_sample(pilot_dir: Path = DEFAULT_PILOT_DIR, seed: int = SELECTION_SEED) -> tuple[Path, Path]:
    frames = read_jsonl(pilot_dir / "semantic_frames_pilot.jsonl")
    variants = read_jsonl(pilot_dir / "variants_dry_run_pilot.jsonl")
    selected = set(select_scenarios(frames, seed))
    rows = [row for row in variants if row["scenario_id"] in selected]
    rows.sort(key=lambda row: (row["scenario_id"], CONDITIONS.index(row["condition"])))
    if len(rows) != 24 or any(sum(r["scenario_id"] == sid for r in rows) != 4 for sid in selected):
        raise ValueError("Pilot sample must contain six complete four-condition scenarios")

    immutable = [
        "review_order", "variant_id", "scenario_id", "population", "binary_label",
        "scenario_family", "style_slot", "condition", "claim",
        "requested_action_category", "entity_placeholders", "text", "warning",
        "final_benchmark_eligible",
    ]
    output_rows = []
    for order, row in enumerate(rows, 1):
        output = {name: row.get(name, "") for name in immutable if name != "review_order"}
        output["review_order"] = order
        output["entity_placeholders"] = json.dumps(output["entity_placeholders"], ensure_ascii=False)
        output.update({field: "" for field in REVIEW_FIELDS})
        output_rows.append({name: output[name] for name in immutable + list(REVIEW_FIELDS)})

    csv_path = pilot_dir / "pilot_review_sample.csv"
    with csv_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(output_rows[0]))
        writer.writeheader()
        writer.writerows(output_rows)
    xlsx_path = pilot_dir / "pilot_review_sample.xlsx"
    create_workbook(output_rows, xlsx_path, seed)
    return csv_path, xlsx_path


def create_workbook(rows: list[dict], path: Path, seed: int) -> None:
    workbook = Workbook()
    review = workbook.active
    review.title = "PilotReview"
    headers = list(rows[0])
    review.append(headers)
    for row in rows:
        review.append([row[name] for name in headers])
    review.freeze_panes = "I2"
    review.auto_filter.ref = f"A1:{get_column_letter(len(headers))}{len(rows)+1}"
    review.sheet_view.showGridLines = False
    for cell in review[1]:
        cell.fill = PatternFill("solid", fgColor="17365D")
        cell.font = Font(color="FFFFFF", bold=True)
        cell.alignment = Alignment(wrap_text=True, vertical="center")
    widths = {"text": 64, "claim": 34, "warning": 38, "review_notes": 38, "rejection_reason": 28}
    for index, name in enumerate(headers, 1):
        review.column_dimensions[get_column_letter(index)].width = widths.get(name, 20)
    for row in review.iter_rows(min_row=2):
        for cell in row:
            cell.alignment = Alignment(wrap_text=True, vertical="top")
    for row_number in range(2, len(rows) + 2):
        review.row_dimensions[row_number].height = 60

    criteria = [name for name in REVIEW_FIELDS if name not in {"action_explicitness_1_to_5", "decision", "rejection_reason", "review_notes", "reviewer_id"}]
    yes_no = DataValidation(type="list", formula1='"yes,no,uncertain"', allow_blank=True)
    decision = DataValidation(type="list", formula1='"approved,rejected,needs_adjudication,pending"', allow_blank=True)
    rating = DataValidation(type="whole", operator="between", formula1="1", formula2="5", allow_blank=True)
    review.add_data_validation(yes_no); review.add_data_validation(decision); review.add_data_validation(rating)
    for name in criteria:
        letter = get_column_letter(headers.index(name) + 1)
        yes_no.add(f"{letter}2:{letter}{len(rows)+1}")
    letter = get_column_letter(headers.index("decision") + 1)
    decision.add(f"{letter}2:{letter}{len(rows)+1}")
    letter = get_column_letter(headers.index("action_explicitness_1_to_5") + 1)
    rating.add(f"{letter}2:{letter}{len(rows)+1}")
    green, red, amber = (PatternFill("solid", fgColor=c) for c in ("C6EFCE", "FFC7CE", "FFEB9C"))
    for name in criteria:
        letter = get_column_letter(headers.index(name) + 1); target = f"{letter}2:{letter}{len(rows)+1}"
        review.conditional_formatting.add(target, CellIsRule(operator="equal", formula=['"yes"'], fill=green))
        review.conditional_formatting.add(target, CellIsRule(operator="equal", formula=['"no"'], fill=red))
        review.conditional_formatting.add(target, CellIsRule(operator="equal", formula=['"uncertain"'], fill=amber))

    instructions = workbook.create_sheet("Instructions")
    text = [
        ("Benchmark v2 pilot review", "Workflow calibration only; not detector evidence and not eligible for final evaluation."),
        ("Selection", f"Six complete scenarios (3 phishing, 3 legitimate), all C0-C3; deterministic seed {seed}. No detector output was used."),
        ("Review unit", "Review all four variants in a scenario together, while recording one decision per variant."),
        ("Semantic intent", "yes only when the same generic claim and communicative purpose are preserved."),
        ("Requested action", "yes only when the requested-action category is preserved; C3 may only soften how directly review/open is requested."),
        ("Label", "yes only when the intended phishing/legitimate label remains unchanged."),
        ("Placeholders", "yes only when placeholders and generic entities are preserved without substitution by real details."),
        ("No operational detail", "yes only when no live URL, phone, credential, payment route, account detail, person, or brand is added."),
        ("Different", "C1-C3 must differ from their parent wording. For C0, judge whether it is a usable anchor and record yes."),
        ("Condition fit", "C0 anchor; C1 minimal normalization; C2 natural direct wording; C3 preserves C2 meaning while making only the review/open request less explicit."),
        ("Explicitness", "Rate action explicitness 1 (implicit) to 5 (very explicit), independently of naturalness."),
        ("Approve", "Use approved only when all categorical criteria are yes and the rating is present."),
        ("Reject", "Use rejected when any criterion is no; copy the exact reason into rejection_reason."),
        ("Adjudicate", "Use needs_adjudication when no criterion is no but at least one is uncertain, or when condition fit is ambiguous."),
        ("Pending", "Blank cells and pending decisions remain pending and are never counted as approvals."),
    ]
    for row in text: instructions.append(row)
    instructions.column_dimensions["A"].width = 23; instructions.column_dimensions["B"].width = 105
    instructions.freeze_panes = "A2"; instructions.sheet_view.showGridLines = False
    for cell in instructions[1]: cell.fill = PatternFill("solid", fgColor="17365D"); cell.font = Font(color="FFFFFF", bold=True)
    for row in instructions.iter_rows():
        for cell in row: cell.alignment = Alignment(wrap_text=True, vertical="top")
    path.parent.mkdir(parents=True, exist_ok=True)
    workbook.save(path)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pilot-dir", type=Path, default=DEFAULT_PILOT_DIR)
    parser.add_argument("--seed", type=int, default=SELECTION_SEED)
    args = parser.parse_args()
    csv_path, xlsx_path = build_sample(args.pilot_dir, args.seed)
    print(f"Review rows: 24 (six complete scenarios)")
    print(f"CSV: {csv_path}\nWorkbook: {xlsx_path}")


if __name__ == "__main__":
    main()
