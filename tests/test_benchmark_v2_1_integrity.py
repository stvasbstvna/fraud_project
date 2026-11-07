from pathlib import Path
import hashlib

import pandas as pd
import yaml
from openpyxl import load_workbook


ROOT = Path(__file__).resolve().parents[1]


def test_full_and_pilot_scales_and_conditions():
    full = pd.read_csv(ROOT / "data/benchmark_v2_1/full/generation_jobs.csv").fillna("")
    pilot = pd.read_csv(ROOT / "data/benchmark_v2_1/pilot/generation_jobs.csv").fillna("")
    assert (len(full), full.frame_id.nunique()) == (8750, 1250)
    assert (len(pilot), pilot.frame_id.nunique()) == (336, 48)
    assert set(full.condition) == {f"C{i}" for i in range(7)}
    assert full.variant_id.is_unique and pilot.variant_id.is_unique
    assert int(pilot.generator_status.eq("not_run").sum()) == 288
    assert full.loc[~full.condition.eq("C0"), "generated_text"].eq("").all()


def test_no_live_urls_or_detector_leakage_columns():
    jobs = pd.read_csv(ROOT / "data/benchmark_v2_1/full/generation_jobs.csv").fillna("")
    assert not jobs.anchor_text.str.contains(r"https?://|\bwww\.", case=False, regex=True).any()
    forbidden = {"prediction", "phishing_probability", "confidence", "detector_score"}
    assert not forbidden.intersection(set(jobs.columns))


def test_synthetic_source_hash_and_authorization_evidence():
    manifest = pd.read_csv(ROOT / "data/benchmark_v2_1/source_manifest.csv").fillna("")
    row = manifest.loc[manifest.source_id.eq("SYNTH-V21")].iloc[0]
    source = ROOT / row.source_file
    assert hashlib.sha256(source.read_bytes()).hexdigest() == row.source_sha256
    assert row.allowed_for_generation == "yes"
    assert row.transformation_permission == "permitted"
    assert row.privacy_review_status == "passed"
    assert (ROOT / row.authorization_evidence_path).exists()


def test_generator_stays_inactive_and_detector_blinded():
    config = yaml.safe_load((ROOT / "configs/benchmark_v2_1_generator.yaml").read_text(encoding="utf-8"))
    assert config["active"] is False
    assert config["generation_authorized"] is False
    assert config["assignment_weight"] == 0.0
    assert config["detector_context"] == "prohibited"
    assert config["detector_guided_retry"] == "prohibited"


def test_pilot_review_is_blank_and_has_no_detector_fields():
    workbook = load_workbook(ROOT / "data/benchmark_v2_1/review/pilot_review_sample_v2_1.xlsx", read_only=True)
    rows = list(workbook["Pilot Review"].iter_rows(values_only=True))
    headers = list(rows[0]); index = {value: i for i, value in enumerate(headers)}
    assert len(rows) - 1 == 336
    assert not any(row[index["reviewer_id"]] for row in rows[1:])
    assert not any(row[index["approve"]] for row in rows[1:])
    assert not any(any(term in str(value).lower() for term in ("prediction", "probability", "confidence", "detector")) for value in headers)
