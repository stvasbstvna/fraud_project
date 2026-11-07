"""Summarize completed Benchmark v2 pilot reviews without treating blanks as approvals."""

from __future__ import annotations

import argparse
import csv
import json
from collections import Counter, defaultdict
from pathlib import Path

from openpyxl import load_workbook
from sklearn.metrics import cohen_kappa_score


DEFAULT_REVIEW = Path("data/benchmark_v2/pilot/pilot_review_sample.csv")
DEFAULT_RESULTS = Path("results/benchmark_v2_pilot")
CONDITIONS = {"C0", "C1", "C2", "C3"}
CRITERIA = {
    "semantic_intent_preserved", "requested_action_preserved", "label_preserved",
    "entities_placeholders_preserved", "no_operational_detail_added",
    "rewrite_is_different", "condition_fit",
}


def enforced_decision(row: dict[str, str]) -> str:
    values = [row.get(name, "").lower() for name in CRITERIA]
    rating = row.get("action_explicitness_1_to_5", "")
    entered = row.get("decision", "").lower()
    if any(value == "no" for value in values):
        calculated = "rejected"
    elif any(value == "uncertain" for value in values):
        calculated = "needs_adjudication"
    elif all(value == "yes" for value in values) and rating in {"1", "2", "3", "4", "5"}:
        calculated = "approved"
    else:
        return "pending"
    if entered in {"", "pending"}:
        return "pending"
    return calculated if entered == calculated else "needs_adjudication"


def load_rows(path: Path) -> list[dict[str, str]]:
    if path.suffix.lower() == ".xlsx":
        workbook = load_workbook(path, read_only=True, data_only=True)
        sheet = workbook["PilotReview"]
        values = list(sheet.iter_rows(values_only=True)); workbook.close()
        headers = [str(value or "") for value in values[0]]
        return [{header: str(value or "").strip() for header, value in zip(headers, row)} for row in values[1:]]
    with path.open(encoding="utf-8-sig", newline="") as handle:
        return [{k: (v or "").strip() for k, v in row.items()} for row in csv.DictReader(handle)]


def resolve(rows: list[dict[str, str]]) -> dict:
    grouped: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in rows:
        grouped[row["variant_id"]].append(row)
    resolved = {}; reasons = Counter()
    for variant_id, reviews in grouped.items():
        decisions = [enforced_decision(r) for r in reviews]
        completed = [d for d in decisions if d not in {"", "pending"}]
        if not completed:
            status = "pending"
        elif "needs_adjudication" in completed or len(set(completed)) > 1:
            status = "adjudication_needed"
        elif all(d == "approved" for d in completed):
            status = "approved"
        elif all(d == "rejected" for d in completed):
            status = "rejected"
        else:
            status = "adjudication_needed"
        resolved[variant_id] = status
        if status == "rejected":
            for review in reviews:
                reason = review.get("rejection_reason", "")
                if reason: reasons[reason] += 1
    counts = Counter(resolved.values())
    scenarios: dict[str, dict[str, str]] = defaultdict(dict)
    for row in rows:
        scenarios[row["scenario_id"]][row["condition"]] = resolved[row["variant_id"]]
    complete_sets = sorted(sid for sid, states in scenarios.items() if set(states) == CONDITIONS and all(v == "approved" for v in states.values()))

    reviewers = sorted({row.get("reviewer_id", "") for row in rows if row.get("reviewer_id", "")})
    agreement = {"calculable": False, "reason": "Fewer than two reviewers with paired categorical decisions."}
    if len(reviewers) >= 2:
        by_reviewer = {reviewer: {r["variant_id"]: enforced_decision(r) for r in rows if r.get("reviewer_id") == reviewer and enforced_decision(r) != "pending"} for reviewer in reviewers}
        common = sorted(set.intersection(*(set(mapping) for mapping in by_reviewer.values())))
        if len(common) >= 2:
            first, second = reviewers[:2]
            agreement = {"calculable": True, "reviewers": [first, second], "paired_variants": len(common), "cohen_kappa": float(cohen_kappa_score([by_reviewer[first][x] for x in common], [by_reviewer[second][x] for x in common]))}
    return {
        "scope": "workflow calibration only; not detector-performance evidence",
        "review_rows": len(rows), "unique_variants": len(grouped),
        "counts": {name: counts.get(name, 0) for name in ("approved", "rejected", "pending", "adjudication_needed")},
        "rejection_reasons_exact": dict(sorted(reasons.items())),
        "complete_approved_condition_sets": complete_sets,
        "agreement": agreement,
    }


def write_summary(review_file: Path, output_dir: Path) -> dict:
    summary = resolve(load_rows(review_file))
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "pilot_review_summary.json").write_text(json.dumps(summary, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    counts = summary["counts"]
    reasons = "\n".join(f"- `{key}`: {value}" for key, value in summary["rejection_reasons_exact"].items()) or "- None recorded."
    agreement = (f"Cohen's kappa: {summary['agreement']['cohen_kappa']:.3f} across {summary['agreement']['paired_variants']} paired variants."
                 if summary["agreement"]["calculable"] else f"Cannot calculate: {summary['agreement']['reason']}")
    text = f"""# Benchmark v2 pilot review summary

> Workflow calibration only. This summary is not detector-performance evidence.

Source review file: `{review_file.as_posix()}`

## Decision counts

- Approved: {counts['approved']}
- Rejected: {counts['rejected']}
- Pending: {counts['pending']}
- Adjudication needed: {counts['adjudication_needed']}
- Complete approved C0-C3 scenario sets: {len(summary['complete_approved_condition_sets'])}

Blank decisions are counted as pending and never as approvals.

## Rejection reasons (exact reviewer entries)

{reasons}

## Agreement

{agreement}
"""
    (output_dir / "pilot_review_summary.md").write_text(text, encoding="utf-8")
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--review-file", type=Path, default=DEFAULT_REVIEW)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_RESULTS)
    args = parser.parse_args()
    summary = write_summary(args.review_file, args.output_dir)
    print(json.dumps(summary["counts"], sort_keys=True))


if __name__ == "__main__":
    main()
