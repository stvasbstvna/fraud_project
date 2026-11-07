from __future__ import annotations

import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from scripts.build_benchmark_v2_freeze_package import build_package


ROOT = Path(__file__).resolve().parents[1]
PROTECTED = ROOT / "data/rewrite_experiment/rewrite_pairs.csv"


class BenchmarkV2FreezePackageTests(unittest.TestCase):
    def test_package_is_deterministic_blocked_and_non_generating(self) -> None:
        before = hashlib.sha256(PROTECTED.read_bytes()).hexdigest()
        with tempfile.TemporaryDirectory(dir=ROOT) as tmp:
            first = Path(tmp) / "first"; second = Path(tmp) / "second"
            result = build_package(first); build_package(second)
            self.assertEqual(result["status"], "BLOCKED_NOT_FROZEN")
            for name in ("power_planning_snapshot.json", "freeze_readiness_report.json", "freeze_readiness_report.md", "generation_authorization.json", "freeze_manifest.json", "prompt_package_snapshot_DRAFT_NOT_FROZEN.md"):
                self.assertEqual((first / name).read_bytes(), (second / name).read_bytes())
            readiness = json.loads((first / "freeze_readiness_report.json").read_text(encoding="utf-8"))
            self.assertFalse(readiness["generation_authorized"])
            self.assertFalse(readiness["message_generation_performed"])
            self.assertFalse(readiness["api_called"])
            self.assertFalse(readiness["detectors_run"])
            codes = {item["code"] for item in readiness["blockers"]}
            self.assertNotIn("c3_direction_conflict", codes)
            self.assertIn("no_active_generator_block", codes)
            self.assertIn("missing_authorized_source_manifest", codes)
        self.assertEqual(before, hashlib.sha256(PROTECTED.read_bytes()).hexdigest())

    def test_manifest_hashes_match_package_files(self) -> None:
        with tempfile.TemporaryDirectory(dir=ROOT) as tmp:
            output = Path(tmp) / "freeze"; build_package(output)
            manifest = json.loads((output / "freeze_manifest.json").read_text(encoding="utf-8"))
            for name, expected in manifest["package_file_sha256"].items():
                self.assertEqual(hashlib.sha256((output / name).read_bytes()).hexdigest(), expected)
            self.assertFalse(manifest["generation_authorized"])


if __name__ == "__main__":
    unittest.main()
