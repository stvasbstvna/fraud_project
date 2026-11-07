from __future__ import annotations

import csv
import json
import tempfile
import unittest
from pathlib import Path

from openpyxl import load_workbook

from scripts.prepare_benchmark_v2_pilot_review import build_sample, select_scenarios
from scripts.summarize_benchmark_v2_pilot_review import resolve, write_summary


ROOT = Path(__file__).resolve().parents[1]
PILOT = ROOT / "data/benchmark_v2/pilot"


class PilotReviewTests(unittest.TestCase):
    def test_selection_is_deterministic_balanced_and_complete(self):
        frames = [json.loads(line) for line in (PILOT / "semantic_frames_pilot.jsonl").read_text(encoding="utf-8").splitlines()]
        first = select_scenarios(frames); second = select_scenarios(frames)
        self.assertEqual(first, second)
        selected = [row for row in frames if row["scenario_id"] in first]
        self.assertEqual(len(first), 6)
        self.assertEqual(sum(row["population"] == "phishing" for row in selected), 3)
        self.assertEqual(sum(row["population"] == "legitimate" for row in selected), 3)
        for population in ("phishing", "legitimate"):
            subset = [row for row in selected if row["population"] == population]
            self.assertEqual(len({row["scenario_family"] for row in subset}), 3)
            self.assertEqual(len({row["style_slot"] for row in subset}), 3)

    def test_sample_has_24_blinded_empty_rows_and_validations(self):
        with tempfile.TemporaryDirectory(dir=ROOT) as tmp:
            target = Path(tmp)
            for name in ("semantic_frames_pilot.jsonl", "variants_dry_run_pilot.jsonl"):
                (target / name).write_bytes((PILOT / name).read_bytes())
            csv_path, xlsx_path = build_sample(target)
            with csv_path.open(encoding="utf-8", newline="") as handle:
                rows = list(csv.DictReader(handle))
            self.assertEqual(len(rows), 24)
            self.assertEqual({sum(r["scenario_id"] == sid for r in rows) for sid in {r["scenario_id"] for r in rows}}, {4})
            self.assertNotIn("detector", " ".join(rows[0]).lower())
            for row in rows:
                self.assertEqual(row["decision"], "")
                self.assertEqual(row["semantic_intent_preserved"], "")
            workbook = load_workbook(xlsx_path)
            self.assertEqual(workbook.sheetnames, ["PilotReview", "Instructions"])
            self.assertEqual(len(workbook["PilotReview"].data_validations.dataValidation), 3)
            workbook.close()

    def test_summary_never_promotes_blanks_and_tracks_exact_reasons(self):
        yes = {name: "yes" for name in ("semantic_intent_preserved", "requested_action_preserved", "label_preserved", "entities_placeholders_preserved", "no_operational_detail_added", "rewrite_is_different", "condition_fit")}
        rows = []
        for condition in ("C0", "C1", "C2", "C3"):
            rows.append({"variant_id": f"A-{condition}", "scenario_id": "A", "condition": condition, "decision": "approved", "rejection_reason": "", "reviewer_id": "r1", "action_explicitness_1_to_5": "3", **yes})
        rows.extend([
            {"variant_id": "B-C0", "scenario_id": "B", "condition": "C0", "decision": "", "rejection_reason": "", "reviewer_id": ""},
            {"variant_id": "B-C1", "scenario_id": "B", "condition": "C1", "decision": "rejected", "rejection_reason": "condition wording changed", "reviewer_id": "r1", "action_explicitness_1_to_5": "3", **{**yes, "condition_fit": "no"}},
            {"variant_id": "B-C2", "scenario_id": "B", "condition": "C2", "decision": "needs_adjudication", "rejection_reason": "", "reviewer_id": "r1", "action_explicitness_1_to_5": "3", **{**yes, "condition_fit": "uncertain"}},
        ])
        summary = resolve(rows)
        self.assertEqual(summary["counts"], {"approved": 4, "rejected": 1, "pending": 1, "adjudication_needed": 1})
        self.assertEqual(summary["rejection_reasons_exact"], {"condition wording changed": 1})
        self.assertEqual(summary["complete_approved_condition_sets"], ["A"])
        self.assertFalse(summary["agreement"]["calculable"])

    def test_summary_files_from_synthetic_csv(self):
        with tempfile.TemporaryDirectory(dir=ROOT) as tmp:
            root = Path(tmp); source = root / "review.csv"
            with source.open("w", encoding="utf-8", newline="") as handle:
                writer = csv.DictWriter(handle, fieldnames=["variant_id", "scenario_id", "condition", "decision", "rejection_reason", "reviewer_id", "action_explicitness_1_to_5", "semantic_intent_preserved", "requested_action_preserved", "label_preserved", "entities_placeholders_preserved", "no_operational_detail_added", "rewrite_is_different", "condition_fit"])
                writer.writeheader(); writer.writerow({"variant_id":"V1","scenario_id":"S1","condition":"C0","decision":"","rejection_reason":"","reviewer_id":""})
            write_summary(source, root / "results")
            self.assertTrue((root / "results/pilot_review_summary.md").exists())
            payload = json.loads((root / "results/pilot_review_summary.json").read_text(encoding="utf-8"))
            self.assertEqual(payload["counts"]["pending"], 1)


if __name__ == "__main__":
    unittest.main()
