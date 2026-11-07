from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[1]


def test_objective_pilot_counts_and_c1_closed_list_are_recorded():
    config = yaml.safe_load((ROOT / "configs/benchmark_v2.yaml").read_text(encoding="utf-8"))
    pilot = config["benchmark"]["populations"]["prompt_development_pilot"]
    assert (pilot["phishing_scenarios"], pilot["legitimate_scenarios"]) == (24, 24)
    register = yaml.safe_load((ROOT / "configs/benchmark_v2_freeze_register.yaml").read_text(encoding="utf-8"))
    c1 = register["benchmark_v2_pre_generation_freeze"]["condition_lineage"]["c1"]
    assert "punctuation" in c1["allowed"]
    assert "lexical_substitution" in c1["prohibited"]


def test_candidate_generator_is_reproducible_but_inactive():
    config = yaml.safe_load((ROOT / "configs/benchmark_v2_generator.yaml").read_text(encoding="utf-8"))
    block = config["generator_blocks"][0]
    assert block["exact_model_version"] == "gpt-5.4-mini-2026-03-17"
    assert block["status"] == "inactive"
    assert block["assignment_weight"] == 0.0
    assert config["generation_authorized"] is False
    assert config["detector_context_prohibited"] is True


def test_signoff_does_not_fabricate_approval():
    text = (ROOT / "docs/benchmark_v2_freeze_signoff.md").read_text(encoding="utf-8")
    assert "[x]" not in text.casefold()
    assert "[ ] Detector-blinded generation authorized" in text


def test_pilot_source_remains_excluded_from_final_generation():
    text = (ROOT / "data/benchmark_v2/source_manifest.csv").read_text(encoding="utf-8")
    assert "pilot_only_not_final_authorized" in text
    assert ",true,false,false," in text


def test_final_decision_package_preserves_all_freeze_gates():
    text = (ROOT / "docs/benchmark_v2_FINAL_DECISION_PACKAGE.md").read_text(encoding="utf-8")
    assert "seven independent approval decisions" in text
    assert "FULL_FREEZE_READY=false" in text
    assert "[x]" not in text.casefold()
    assert "gpt-5.4-mini-2026-03-17" in text
    assert "Reviewer A" in text and "Reviewer B" in text
