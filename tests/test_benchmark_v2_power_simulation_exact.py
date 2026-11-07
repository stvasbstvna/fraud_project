from pathlib import Path

import pandas as pd

from analysis.benchmark_v2_power_simulation import build_outputs, exact_mcnemar_p, holm_rejections


def test_exact_mcnemar_known_values():
    assert exact_mcnemar_p(0, 0) == 1.0
    assert exact_mcnemar_p(0, 6) == 0.03125
    assert exact_mcnemar_p(3, 3) == 1.0


def test_holm_stepdown_stops_after_first_failure():
    result = holm_rejections([0.001, 0.009, 0.010, 0.5, 0.6, 0.7, 0.8])
    assert result.tolist() == [True, False, False, False, False, False, False]


def test_outputs_are_deterministic_and_labeled_sensitivity(tmp_path: Path):
    a = tmp_path / "a"; b = tmp_path / "b"
    build_outputs(a, simulations=40, seed=7)
    build_outputs(b, simulations=40, seed=7)
    assert (a / "power_simulation.csv").read_bytes() == (b / "power_simulation.csv").read_bytes()
    frame = pd.read_csv(a / "power_simulation.csv")
    assert len(frame) == 9 * 7
    assert set(frame.analysis_role) == {"sensitivity_not_confirmatory"}
    assert (a / "power_summary.json").exists()


def test_custom_approved_candidate_inputs_are_parameterized(tmp_path: Path):
    build_outputs(
        tmp_path, simulations=20, seed=9,
        profiles={"approved_candidate_inputs": (0.04, 0.10)},
        sample_sizes=(750,),
    )
    frame = pd.read_csv(tmp_path / "power_simulation.csv")
    assert set(frame.profile) == {"approved_candidate_inputs"}
    assert set(frame.n_scenarios) == {750}
    assert len(frame) == 7
