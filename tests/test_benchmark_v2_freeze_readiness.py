import json
from pathlib import Path

from scripts.check_benchmark_v2_freeze_readiness import build_report, write_report


def test_readiness_is_honest_about_human_blockers():
    report = build_report()
    assert report["full_freeze_ready"] is False
    assert report["generation_authorized"] is False
    assert report["counts"]["missing_generator_assignment"] >= 1
    assert report["counts"]["missing_source_authorizations"] >= 1
    assert report["counts"]["incomplete_human_review"] >= 1
    assert report["safety_attestation"] == {
        "messages_generated": False, "apis_called": False, "detectors_run": False
    }


def test_readiness_outputs_machine_readable_report(tmp_path: Path):
    report = build_report()
    json_path, md_path = tmp_path / "report.json", tmp_path / "report.md"
    write_report(report, json_path, md_path)
    loaded = json.loads(json_path.read_text(encoding="utf-8"))
    assert loaded["status"] == report["status"]
    assert "Full freeze ready" in md_path.read_text(encoding="utf-8")
