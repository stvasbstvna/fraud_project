from __future__ import annotations

import csv
import hashlib
import json
import re
import tempfile
import unittest
from collections import Counter, defaultdict
from pathlib import Path

from scripts.build_benchmark_v2_pilot import PHISHING_PLACEHOLDERS, REVIEW_FIELDS, build_pilot


ROOT = Path(__file__).resolve().parents[1]
PROTECTED_V1 = ROOT / "data/rewrite_experiment/rewrite_pairs.csv"


def read_jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


class BenchmarkV2PilotTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory(dir=ROOT)
        self.output = Path(self.temp.name) / "pilot"
        self.v1_before = hashlib.sha256(PROTECTED_V1.read_bytes()).hexdigest()
        self.counts = build_pilot(self.output)
        self.frames = read_jsonl(self.output / "semantic_frames_pilot.jsonl")
        self.variants = read_jsonl(self.output / "variants_dry_run_pilot.jsonl")
        self.jobs = read_jsonl(self.output / "generation_jobs_not_run.jsonl")

    def tearDown(self) -> None:
        self.temp.cleanup()

    def test_exact_frame_balance_and_family_style_design(self) -> None:
        self.assertEqual(self.counts["frames"], 48)
        self.assertEqual(Counter(frame["population"] for frame in self.frames), {"phishing": 24, "legitimate": 24})
        for population in ("phishing", "legitimate"):
            selected = [frame for frame in self.frames if frame["population"] == population]
            families: dict[str, set[str]] = defaultdict(set)
            for frame in selected:
                families[frame["scenario_family"]].add(frame["style_slot"])
            self.assertEqual(len(families), 6)
            self.assertTrue(all(slots == {"brief", "plain", "routine", "conversational"} for slots in families.values()))

    def test_exact_unique_variants_and_required_markers(self) -> None:
        self.assertEqual(len(self.variants), 192)
        self.assertEqual(len({row["variant_id"] for row in self.variants}), 192)
        self.assertEqual(len({row["text"] for row in self.variants}), 192)
        grouped = Counter((row["scenario_id"], row["condition"]) for row in self.variants)
        self.assertEqual(len(grouped), 192)
        self.assertTrue(all(count == 1 for count in grouped.values()))
        self.assertTrue(all(row["creation_method"] == "researcher_authored_nonoperational_dry_run" for row in self.variants))
        self.assertTrue(all(row["generator_metadata"] is None and row["prompt_id"] is None for row in self.variants))
        self.assertTrue(all(row["human_review_status"] == "pending" and row["final_benchmark_eligible"] is False for row in self.variants))
        self.assertTrue(all("PILOT-ONLY" in row["warning"] for row in self.variants))

    def test_condition_relationships(self) -> None:
        by_scenario: dict[str, dict[str, dict]] = defaultdict(dict)
        for row in self.variants:
            by_scenario[row["scenario_id"]][row["condition"]] = row
        for conditions in by_scenario.values():
            self.assertEqual(set(conditions), {"C0", "C1", "C2", "C3"})
            self.assertNotEqual(conditions["C0"]["text"], conditions["C1"]["text"])
            self.assertNotEqual(conditions["C3"]["text"], conditions["C2"]["text"])
            self.assertIn("please open", conditions["C2"]["text"].lower())
            self.assertNotIn("please open", conditions["C3"]["text"].lower())
            self.assertIn("details are available", conditions["C3"]["text"].lower())

    def test_jobs_are_unrun_and_detector_blinded(self) -> None:
        self.assertEqual(len(self.jobs), 144)
        self.assertTrue(all(job["target_condition"] in {"C1", "C2", "C3"} for job in self.jobs))
        self.assertTrue(all(job["status"] == "not_run" and job["detector_access"] == "prohibited" for job in self.jobs))

    def test_no_live_or_operational_details(self) -> None:
        text = "\n".join(row["text"] for row in self.variants)
        self.assertNotRegex(text, re.compile(r"(?i)https?://|www\.|\b[\w.+-]+@[\w.-]+\.\w{2,}\b"))
        self.assertNotRegex(text, re.compile(r"(?<!\w)\+?\d[\d ()-]{6,}\d(?!\w)"))
        self.assertNotRegex(text, re.compile(r"(?i)\b(?:password|credential|account number|routing number|wire transfer|gift card)\b"))
        allowed = set(PHISHING_PLACEHOLDERS)
        for row in self.variants:
            placeholders = set(re.findall(r"\[[A-Z-]+\]", row["text"]))
            self.assertTrue(placeholders.issubset(allowed))
            if row["population"] == "legitimate":
                self.assertIn("official app", row["text"].lower())
                self.assertFalse(placeholders)

    def test_review_queue_has_empty_review_fields(self) -> None:
        with (self.output / "human_review_queue.csv").open(encoding="utf-8", newline="") as handle:
            rows = list(csv.DictReader(handle))
        self.assertEqual(len(rows), 192)
        self.assertTrue(all(all(row[field] == "" for field in REVIEW_FIELDS) for row in rows))

    def test_sha256_manifest_matches_every_listed_file(self) -> None:
        checksums = json.loads((self.output / "SHA256SUMS.json").read_text(encoding="utf-8"))
        self.assertNotIn("SHA256SUMS.json", checksums)
        self.assertEqual(set(checksums), {"semantic_frames_pilot.jsonl", "variants_dry_run_pilot.jsonl", "generation_jobs_not_run.jsonl", "human_review_queue.csv", "source_manifest_pilot.jsonl", "README.md"})
        for name, expected in checksums.items():
            self.assertEqual(hashlib.sha256((self.output / name).read_bytes()).hexdigest(), expected)

    def test_build_is_deterministic_and_does_not_touch_benchmark_v1(self) -> None:
        second = Path(self.temp.name) / "pilot-second"
        build_pilot(second)
        for name in json.loads((self.output / "SHA256SUMS.json").read_text(encoding="utf-8")):
            self.assertEqual((self.output / name).read_bytes(), (second / name).read_bytes())
        self.assertEqual(self.v1_before, hashlib.sha256(PROTECTED_V1.read_bytes()).hexdigest())


if __name__ == "__main__":
    unittest.main()
