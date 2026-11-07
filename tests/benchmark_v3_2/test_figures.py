"""Figure contracts tested with a tiny, deliberately nonuniform paired cohort."""
import json
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from src.benchmark_v3_2.figures import META_FIELDS, bootstrap_frame_mean, generate


def _csv(root, path, data):
    target = root / path
    target.parent.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(data).to_csv(target, index=False)


@pytest.fixture
def inputs(tmp_path):
    matrix, distances, attempts = [], [], []
    for frame in range(5):
        for condition in ["C0", "C1", "C2"]:
            if frame == 4 and condition == "C2":
                continue
            matrix.append(dict(frame_id=f"f{frame}", condition=condition, true_label=frame % 2,
                               text=f"Frame {frame}, condition {condition}", primary_complete_case=frame < 4,
                               source_dataset="fixture", template_family_id=f"t{frame}"))
            distances.append(dict(frame_id=f"f{frame}", condition=condition,
                                  true_label=frame % 2, primary_complete_case=frame < 4,
                                  token_jaccard=.9, normalized_edit_distance=.1,
                                  frozen_tfidf_cosine_similarity=.95, surface_distance=int(condition[-1]) * .2,
                                  semantic_similarity_if_available=np.nan, semantic_preserved=True))
            attempts.append(dict(frame_id=f"f{frame}", condition=condition, attempt=1, status="accepted"))
    attempts.append(dict(frame_id="f0", condition="C1", attempt=2, status="rejected"))
    _csv(tmp_path, "data/benchmark_v3_2/frozen/robustness_matrix.csv", matrix)
    _csv(tmp_path, "data/benchmark_v3_2/generated/attempts.csv", attempts)
    _csv(tmp_path, "results/benchmark_v3_2/manipulation/per_variant_distances.csv", distances)
    _csv(tmp_path, "results/benchmark_v3_2/tables/cohort_flow.csv", [dict(stage="source records", count=10), dict(stage="primary complete frames", count=4)])
    for model_index, model in enumerate(["LR", "RF", "ModernBERT"]):
        rows = []
        for row in matrix:
            frame = int(row["frame_id"][1:])
            baseline = .8 if frame % 2 else .3
            if frame == 4:
                baseline = .9
            delta = int(row["condition"][-1]) * (.02 + .03 * frame + .01 * model_index)
            if frame == 3 and row["condition"] == "C2":
                delta = .35 + .01 * model_index
            if frame == 4 and row["condition"] == "C1":
                delta = .5
            probability = baseline - delta
            rows.append(dict(frame_id=row["frame_id"], condition=row["condition"], probability=probability,
                             prediction=int(probability >= .5), C0_probability=baseline,
                             signed_delta=delta, absolute_delta=abs(delta), threshold_transition="unchanged", surface_distance=.999))
        _csv(tmp_path, f"results/benchmark_v3_2/predictions/{model}_predictions.csv", rows)
    return tmp_path


def test_complete_suite_exact_data_and_safe_repeat(inputs):
    paths = generate(inputs, bootstrap_draws=100)
    assert len(paths) == 12
    directory = inputs / "results/benchmark_v3_2/figures"
    before = {path.name: path.read_bytes() for path in directory.iterdir()}
    for path in paths:
        slug = path.stem
        metadata = json.loads((directory / f"{slug}_metadata.json").read_text(encoding="utf-8"))
        assert META_FIELDS <= metadata.keys()
        assert metadata["N"]["primary_complete_frames"] == 4
        assert (directory / f"{slug}.svg").stat().st_size > 500
        assert (directory / f"{slug}_data.csv").is_file()
    delta = pd.read_csv(directory / "05_signed_delta_data.csv")
    expected = np.mean([.02 + .03 * f for f in [1, 3]])
    assert delta.query("model == 'LR' and condition == 'C1' and true_label == 1")["mean"].iloc[0] == pytest.approx(expected)
    assert (delta.N == 2).all()
    assert set(delta.true_label) == {0, 1}
    assert (delta.bootstrap_seed == 42).all()
    assert (delta.ci_low <= delta["mean"]).all()
    assert (delta.ci_high >= delta["mean"]).all()
    rates = pd.read_csv(directory / "03_recall_data.csv")
    assert (rates.N == 2).all()
    transitions = pd.read_csv(directory / "08_threshold_transitions_data.csv")
    assert set(transitions.transition_type) == {"detected_to_missed", "missed_to_detected", "legit_to_FP", "FP_to_legit"}
    crossings = transitions.query("condition == 'C2' and transition_type == 'detected_to_missed'")
    assert (crossings["count"] == 1).all()
    assert (crossings.N == 2).all()
    assert (crossings.eligible_N == 2).all()
    assert (crossings.rate == .5).all()
    representative = pd.read_csv(directory / "09_representative_frame_data.csv")
    assert representative.frame_id.nunique() == 1
    assert set(representative.condition) == {"C0", "C1", "C2"}
    assert representative.frame_id.iloc[0] in {"f1", "f2"}
    extreme = pd.read_csv(directory / "10_extreme_case_data.csv")
    assert set(extreme.frame_id) == {"f4"}
    assert not extreme.primary_complete_case.any()
    assert (extreme.threshold == .5).all()
    assert extreme.before_text.str.contains("condition C0").all()
    assert (extreme.after_text == extreme.text).all()
    scatter = pd.read_csv(directory / "07_distance_vs_movement_data.csv")
    assert "surface_distance_x" not in scatter
    assert set(scatter.surface_distance) == {0, .2, .4}
    completeness = pd.read_csv(directory / "02_condition_completeness_data.csv").set_index("condition")
    assert pd.isna(completeness.loc["C0", "generated_slots"])
    assert completeness.loc["C1", "generated_slots"] == 5
    assert completeness.loc["C1", "approved_slots"] == 5
    assert completeness.loc["C1", "rejected_slots"] == 0
    assert completeness.loc["C1", "retry_count"] == 1
    semantic = pd.read_csv(directory / "M2_semantic_preservation_data.csv")
    assert semantic.semantic_similarity_if_available.isna().all()
    assert set(semantic.plotted_y) == {1.0}
    assert "unavailable" in json.loads((directory / "M2_semantic_preservation_metadata.json").read_text())["main_observation"]
    generate(inputs, bootstrap_draws=100)
    assert before == {path.name: path.read_bytes() for path in directory.iterdir()}
    target = directory / "05_signed_delta_data.csv"
    target.write_text("tampered", encoding="utf-8")
    with pytest.raises(FileExistsError, match="overwrite"):
        generate(inputs, bootstrap_draws=100)
    assert target.read_text() == "tampered"


def test_missing_primary_prediction_is_error_not_zero(inputs):
    path = inputs / "results/benchmark_v3_2/predictions/LR_predictions.csv"
    data = pd.read_csv(path)
    data = data[~((data.frame_id == "f0") & (data.condition == "C1"))]
    data.to_csv(path, index=False)
    with pytest.raises(ValueError, match="Missing primary predictions"):
        generate(inputs, bootstrap_draws=10)


def test_bootstrap_resamples_frames_together():
    # Two rows from frame A must move together in each bootstrap draw.
    data = pd.DataFrame({"frame_id": ["a", "a", "b"], "value": [0.0, 0.0, 1.0]})
    mean, low, high = bootstrap_frame_mean(data, "value", draws=1000)
    assert mean == pytest.approx(1 / 3)
    assert low == 0
    assert high == 1
    assert bootstrap_frame_mean(data, "value", draws=1000) == (mean, low, high)


@pytest.mark.parametrize("retain_phishing", [False, True])
def test_empty_cohort_or_class_is_annotated_and_never_zero_estimate(inputs, retain_phishing):
    path = inputs / "data/benchmark_v3_2/frozen/robustness_matrix.csv"
    matrix = pd.read_csv(path)
    matrix["primary_complete_case"] = (matrix.true_label == 1) & matrix.primary_complete_case if retain_phishing else False
    matrix.to_csv(path, index=False)
    assert len(generate(inputs, bootstrap_draws=30)) == 12
    directory = inputs / "results/benchmark_v3_2/figures"
    delta = pd.read_csv(directory / "05_signed_delta_data.csv")
    legitimate = delta[delta.true_label == 0]
    assert (legitimate.N == 0).all()
    assert legitimate[["mean", "ci_low", "ci_high"]].isna().all().all()
    rates = pd.read_csv(directory / "04_false_positive_rate_data.csv")
    assert (rates.N == 0).all()
    assert rates.rate.isna().all()
    for slug in ["M1_distance_distributions", "M2_semantic_preservation"]:
        manipulation = pd.read_csv(directory / f"{slug}_data.csv")
        assert not manipulation.empty
        assert "f4" in set(manipulation.frame_id)
        assert "C0" not in set(manipulation.condition)
        metadata = json.loads((directory / f"{slug}_metadata.json").read_text())
        assert "all approved available" in metadata["filters"]
    if not retain_phishing:
        scatter = pd.read_csv(directory / "07_distance_vs_movement_data.csv")
        assert len(scatter) == 27  # nine observed nonbaseline slots × three models
        assert scatter.surface_distance.notna().all()
        scatter_meta = json.loads((directory / "07_distance_vs_movement_metadata.json").read_text())
        assert "exploratory" in scatter_meta["title"]
        assert "available" in scatter_meta["filters"]
        metadata = json.loads((directory / "09_representative_frame_metadata.json").read_text())
        assert metadata["N"]["primary_complete_frames"] == 0
        assert "unavailable" in metadata["main_observation"]
