"""Auditable, presentation-ready figures for the expanded robustness experiment.

Every mark is backed by a sibling CSV. Existing artifacts are immutable: reruns
accept byte-identical content only. No unavailable observation is filled with zero.
"""
from __future__ import annotations

import argparse
import io
import inspect
import json
from datetime import datetime, timezone
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

MODELS = ("LR", "RF", "ModernBERT")
META_FIELDS = {"title", "research_question", "source_data", "filters", "N", "models", "conditions", "x_axis", "y_axis", "main_observation", "allowed_interpretation", "forbidden_interpretation", "generated_at", "script"}


def _write(path: Path, content: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        if path.read_bytes() != content:
            raise FileExistsError(f"Refusing to overwrite different figure artifact: {path}")
        return
    with path.open("xb") as handle:
        handle.write(content)


def _bool(values: pd.Series) -> pd.Series:
    return values.astype(str).str.strip().str.lower().isin(["true", "1", "yes"])


def _labels(values: pd.Series) -> pd.Series:
    mapped = values.astype(str).str.lower().map({"0": 0, "0.0": 0, "1": 1, "1.0": 1, "phishing": 1, "smishing": 1, "spam": 1, "fraud": 1, "legitimate": 0, "benign": 0, "ham": 0})
    if mapped.isna().any():
        raise ValueError("Unrecognized true_label or prediction values")
    return mapped.astype(int)


def bootstrap_frame_mean(data: pd.DataFrame, value: str, *, seed: int = 42, draws: int = 2000) -> tuple[float, float, float]:
    """Resample frame IDs, preserving all observations belonging to a frame."""
    valid = data[["frame_id", value]].dropna()
    if valid.empty:
        return float("nan"), float("nan"), float("nan")
    grouped = valid.groupby("frame_id")[value].agg(["sum", "count"])
    rng = np.random.default_rng(seed)
    indices = rng.integers(0, len(grouped), size=(draws, len(grouped)))
    estimates = grouped["sum"].to_numpy()[indices].sum(axis=1) / grouped["count"].to_numpy()[indices].sum(axis=1)
    return float(valid[value].mean()), *np.quantile(estimates, [0.025, 0.975]).tolist()


def _load(root: Path):
    matrix_path = root / "data/benchmark_v3_2/frozen/robustness_matrix.csv"
    matrix = pd.read_csv(matrix_path)
    if matrix.duplicated(["frame_id", "condition"]).any():
        raise ValueError("Duplicate matrix frame-condition rows")
    matrix["primary_complete_case"] = _bool(matrix["primary_complete_case"])
    matrix["true_label"] = _labels(matrix.true_label)
    primary = matrix[matrix.primary_complete_case].copy()
    conditions = sorted(matrix.condition.unique())
    if "C0" not in conditions:
        raise ValueError("C0 baseline condition is required")
    expected = set(conditions)
    if any(set(g.condition) != expected for _, g in primary.groupby("frame_id")):
        raise ValueError("Primary complete-case frame is missing a condition")
    frames = primary.frame_id.nunique()
    predictions = []
    sources = [str(matrix_path.relative_to(root))]
    for model in MODELS:
        path = root / f"results/benchmark_v3_2/predictions/{model}_predictions.csv"
        pred = pd.read_csv(path)
        if pred.duplicated(["frame_id", "condition"]).any():
            raise ValueError(f"Duplicate predictions for {model}")
        probability = next((c for c in ["probability", "phishing_probability", "p_phishing", "probability_phishing", "P_phishing"] if c in pred), None)
        if probability is None:
            raise ValueError(f"No phishing probability column for {model}")
        pred = pred.rename(columns={probability: "probability"})
        # Frozen matrix is authoritative for labels and cohort membership.
        pred = pred.drop(columns=[c for c in ["true_label", "primary_complete_case", "text", "source_dataset", "template_family_id"] if c in pred])
        joined = matrix.merge(pred, on=["frame_id", "condition"], how="left", validate="one_to_one")
        required = ["probability", "prediction", "C0_probability", "signed_delta", "absolute_delta", "threshold_transition"]
        if joined.loc[joined.primary_complete_case, required].isna().any().any():
            raise ValueError(f"Missing primary predictions for {model}; never fill missing values with zero")
        joined = joined.dropna(subset=required).copy()
        joined["prediction"] = _labels(joined.prediction)
        joined["model"] = model
        predictions.append(joined)
        sources.append(str(path.relative_to(root)))
    available = pd.concat(predictions, ignore_index=True)
    return matrix, available[available.primary_complete_case].copy(), available, conditions, frames, sources


def generate(root: str | Path = ".", *, bootstrap_draws: int = 2000) -> list[Path]:
    root = Path(root).resolve()
    matrix, data, available, conditions, n_frames, sources = _load(root)
    out = root / "results/benchmark_v3_2/figures"
    out.mkdir(parents=True, exist_ok=True)
    # Stable timestamps make a repeat invocation check-identical rather than rewrite.
    existing_metadata = next(out.glob("*_metadata.json"), None)
    timestamp = json.loads(existing_metadata.read_text(encoding="utf-8"))["generated_at"] if existing_metadata else datetime.now(timezone.utc).isoformat()
    plt.rcParams.update({"font.size": 10, "axes.spines.top": False, "axes.spines.right": False, "svg.hashsalt": "benchmark-v3.2"})
    catalog, notes, outputs = [], [], []

    def save(slug, title, question, table, draw, x, y, observation, allowed, forbidden, *, filters="primary_complete_case == True", extra_sources=()):
        fig, ax = plt.subplots(figsize=(10, 5.8), layout="constrained")
        draw(ax)
        if n_frames == 0 and filters == "primary_complete_case == True":
            ax.text(.5, .5, "No primary complete frames; estimates unavailable", transform=ax.transAxes, ha="center", bbox={"facecolor": "white", "alpha": .9})
            observation = "No primary complete frames; estimates are unavailable. " + observation
        ax.set(title=title, xlabel=x, ylabel=y)
        fig.text(.99, .005, f"Primary complete frames: {n_frames} | source values in {slug}_data.csv", ha="right", fontsize=8)
        metadata = dict(title=title, research_question=question, source_data=list(sources) + list(extra_sources), filters=filters,
                        N={"primary_complete_frames": int(n_frames), "plotted_rows": int(len(table)), "distinct_frames_in_data": int(table.frame_id.nunique()) if "frame_id" in table else None}, models=sorted(table.model.unique().tolist()) if "model" in table else [],
                        conditions=sorted(table.condition.unique().tolist()) if "condition" in table else conditions, x_axis=x, y_axis=y,
                        main_observation=observation, allowed_interpretation=allowed, forbidden_interpretation=forbidden,
                        generated_at=timestamp, script="src/benchmark_v3_2/figures.py")
        artifacts = {f"{slug}_data.csv": table.to_csv(index=False, lineterminator="\n").encode(), f"{slug}_metadata.json": (json.dumps(metadata, indent=2, ensure_ascii=False) + "\n").encode()}
        for extension in ["png", "svg"]:
            buffer = io.BytesIO()
            fig.savefig(buffer, format=extension, dpi=170, metadata={"Software": "benchmark_v3_2"} if extension == "png" else {"Date": None, "Creator": "benchmark_v3_2"})
            artifacts[f"{slug}.{extension}"] = buffer.getvalue()
        plt.close(fig)
        # Validate all siblings before writing any of this figure's artifacts.
        for name, payload in artifacts.items():
            if (out / name).exists() and (out / name).read_bytes() != payload:
                raise FileExistsError(f"Refusing to overwrite different figure artifact: {out / name}")
        for name, payload in artifacts.items():
            _write(out / name, payload)
        outputs.append(out / f"{slug}.png")
        catalog.append(f"## {title}\n\n![{title}](figures/{slug}.png)\n\nQuestion: {question}\n\nObservation: {observation}\n\nAllowed: {allowed}\n\nDo not claim: {forbidden}\n\nData: [CSV](figures/{slug}_data.csv). Audit: [metadata](figures/{slug}_metadata.json).\n")
        notes.append(f"## {title} (20–40 seconds)\n\n{question} {observation} {allowed} {forbidden}\n")

    def grouped_bars(ax, table, value, *, uncertainty=False):
        for i, model in enumerate(MODELS):
            rows = table[table.model == model].set_index("condition").reindex(conditions)
            positions = np.arange(len(conditions)) + (i - 1) * .24
            ax.bar(positions, rows[value], width=.23, label=model)
            if uncertainty:
                ax.errorbar(positions, rows[value], yerr=np.array([rows[value] - rows.ci_low, rows.ci_high - rows[value]]), fmt="none", color="black", capsize=3)
        ax.set_xticks(np.arange(len(conditions)), conditions, rotation=20)
        ax.legend()

    flow_path = root / "results/benchmark_v3_2/tables/cohort_flow.csv"
    flow = pd.read_csv(flow_path)
    save("01_source_flow", "Source and cohort flow", "How many records reach each cohort stage?", flow,
         lambda ax: (ax.barh(flow.stage, flow["count"]), ax.invert_yaxis()), "Records / frames (as named by stage)", "Cohort stage",
         "; ".join(f"{r.stage}: {r.count}" for r in flow.itertuples()), "Counts describe cohort selection; consult stage units.", "Selection counts do not establish population prevalence.", filters="all cohort flow stages", extra_sources=[str(flow_path.relative_to(root))])

    attempt_path = root / "data/benchmark_v3_2/generated/attempts.csv"
    attempts = pd.read_csv(attempt_path)
    completeness = matrix.groupby("condition").agg(available_frames=("frame_id", "nunique"), primary_complete_frames=("primary_complete_case", "sum")).reset_index()
    slot_rows = []
    for condition in conditions:
        part = attempts[attempts.condition == condition]
        if condition == "C0":
            slot_rows.append(dict(condition=condition, planned_slots=np.nan, generated_slots=np.nan, approved_slots=np.nan, rejected_slots=np.nan, attempt_count=0, retry_count=0))
            continue
        statuses = part.status.astype(str).str.lower()
        generated = _bool(part.generated) if "generated" in part else statuses.isin(["accepted", "approved", "rejected"])
        approved = statuses.isin(["accepted", "approved"])
        generated_ids = set(part.loc[generated, "frame_id"])
        approved_ids = set(part.loc[approved, "frame_id"])
        rejected_ids = set(part.loc[statuses.isin(["rejected", "failed"]), "frame_id"]) - approved_ids
        slots = part.frame_id.nunique()
        slot_rows.append(dict(condition=condition, planned_slots=slots, generated_slots=len(generated_ids), approved_slots=len(approved_ids), rejected_slots=len(rejected_ids), attempt_count=len(part), retry_count=len(part) - slots))
    completeness = completeness.merge(pd.DataFrame(slot_rows), on="condition", how="left")
    def draw_completeness(ax):
        for offset, column, label in [(-.27, "generated_slots", "Generated slots"), (-.09, "approved_slots", "Approved slots"), (.09, "rejected_slots", "Rejected slots"), (.27, "primary_complete_frames", "Complete frames")]:
            ax.bar(np.arange(len(completeness)) + offset, completeness[column], .17, label=label)
        ax.set_xticks(np.arange(len(completeness)), completeness.condition, rotation=20)
        ax.text(.01, .98, "C0 is the source condition: no generation. Retries counted separately in CSV.", va="top", transform=ax.transAxes, fontsize=8)
        ax.legend(fontsize=8)
    save("02_condition_completeness", "Condition completeness", "Which conditions are available and included in the paired cohort?", completeness,
         draw_completeness, "Condition", "Unique frame-condition slots / complete frames", f"{n_frames} frames are retained in every condition. Generated/approved/rejected counts deduplicate retries; rejected means no approved attempt for that slot.", "Availability and attempts are separate quantities; attempt_count and retry_count are exported separately. C0 has no generated slots.", "A missing condition is never a zero detector score.", filters="all matrix rows and initial frame-condition slots; attempts including retries counted separately", extra_sources=[str(attempt_path.relative_to(root))])

    for slug, label, truth in [("03_recall", "Recall", 1), ("04_false_positive_rate", "False positive rate", 0)]:
        rows = []
        for model in MODELS:
            for condition in conditions:
                subset = data[(data.model == model) & (data.condition == condition) & (data.true_label == truth)]
                rows.append(dict(model=model, condition=condition, N=len(subset), positive_predictions=int(subset.prediction.sum()), rate=float(subset.prediction.mean()) if len(subset) else np.nan))
        table = pd.DataFrame(rows)
        def draw_rate(ax, t=table):
            grouped_bars(ax, t, "rate")
            ax.set_ylim(0, 1.12)
            for i, model in enumerate(MODELS):
                for j, c in enumerate(conditions):
                    r = t[(t.model == model) & (t.condition == c)].iloc[0]
                    ax.text(j + (i - 1) * .24, (r.rate if pd.notna(r.rate) else 0) + .02, f"N={r.N}" if r.N else "N=0; NA", ha="center", fontsize=7, rotation=90)
        save(slug, f"{label} by condition", f"How does {label.lower()} vary by model and condition?", table, draw_rate, "Condition", label,
             f"Denominators are explicitly shown for true_label={truth}; undefined rates remain missing.", "Rates compare the same complete frames within each true-label stratum.", "These rates do not estimate deployment prevalence or causal effects.")

    for slug, value, title in [("05_signed_delta", "signed_delta", "Signed phishing-probability movement (P0 − Pi)"), ("06_absolute_delta", "absolute_delta", "Absolute phishing-probability movement |P0 − Pi|")]:
        rows = []
        for truth in [0, 1]:
            for model in MODELS:
                for condition in conditions:
                    group = data[(data.true_label == truth) & (data.model == model) & (data.condition == condition)]
                    mean, low, high = bootstrap_frame_mean(group, value, draws=bootstrap_draws)
                    rows.append(dict(model=model, condition=condition, true_label=truth, N=group.frame_id.nunique(), mean=mean, ci_low=low, ci_high=high, bootstrap_seed=42, bootstrap_draws=bootstrap_draws, bootstrap_unit="frame_id"))
        table = pd.DataFrame(rows)
        def draw_movement(ax, t=table):
            for truth, offset, marker in [(0, -.05, "s"), (1, .05, "o")]:
                for i, model in enumerate(MODELS):
                    subset = t[(t.true_label == truth) & (t.model == model)].set_index("condition").reindex(conditions)
                    valid = subset["mean"].notna()
                    positions = np.arange(len(conditions)) + (i - 1) * .24 + offset
                    label = f"{model}: {'legitimate' if truth == 0 else 'phishing'} (N={int(subset.N.iloc[0])})"
                    ax.errorbar(positions[valid], subset.loc[valid, "mean"], yerr=np.array([subset.loc[valid, "mean"] - subset.loc[valid, "ci_low"], subset.loc[valid, "ci_high"] - subset.loc[valid, "mean"]]), fmt=marker, capsize=3, label=label)
            ax.set_xticks(np.arange(len(conditions)), conditions, rotation=20)
            ax.axhline(0, color="grey", lw=.7)
            ax.legend(fontsize=8, ncol=2)
        save(slug, title, "How large is paired movement relative to C0 within each true class?", table, draw_movement, "Condition", "Class-specific mean movement (95% frame bootstrap interval)",
             "Legitimate and phishing observations are labelled separately; a class with N=0 has no estimate. Positive signed movement means lower phishing probability than C0. Intervals resample frames with seed 42.", "This describes paired score sensitivity within each class for retained frames.", "Probability movement alone does not establish evasion, correctness, or semantic equivalence.")

    distance_path = root / "results/benchmark_v3_2/manipulation/per_variant_distances.csv"
    distances = pd.read_csv(distance_path)
    if distances.duplicated(["frame_id", "condition"]).any():
        raise ValueError("Duplicate distance rows")
    distance_columns = [c for c in distances if c not in ["true_label", "primary_complete_case"]]
    distance_only = distances[distance_columns]
    scatter_base = data if n_frames else available[available.condition != "C0"].copy()
    scatter_filter = "primary_complete_case == True" if n_frames else "all approved available non-C0 pairs; exploratory association because primary complete cohort is empty"
    overlap = [c for c in distance_only if c in scatter_base and c not in ["frame_id", "condition"]]
    scatter = scatter_base.drop(columns=overlap).merge(distance_only, on=["frame_id", "condition"], how="left", validate="many_to_one")
    def draw_scatter(ax):
        for model in MODELS:
            rows = scatter[scatter.model == model].dropna(subset=["surface_distance", "absolute_delta"])
            ax.scatter(rows.surface_distance, rows.absolute_delta, s=13, alpha=.45, label=model)
        ax.legend()
    scatter_title = "Surface distance versus score movement" + (" (available pairs; exploratory)" if not n_frames else "")
    save("07_distance_vs_movement", scatter_title, "Do larger surface changes accompany larger score changes?", scatter, draw_scatter,
         "Surface distance", "Absolute phishing-probability movement", f"{scatter.surface_distance.notna().sum()} model-variant observations have surface distance; missing distances are omitted from marks.",
         "The plot describes association, with repeated observations belonging to frames. When the primary cohort is empty, these are explicitly exploratory available-pair observations.", "Association is not causation; surface distance is not semantic distance. Available-pair observations are not complete-cohort inference.", filters=scatter_filter, extra_sources=[str(distance_path.relative_to(root))])

    transitions = data.copy()
    baseline_prediction = data[data.condition == "C0"][["frame_id", "model", "prediction"]].rename(columns={"prediction": "baseline_prediction"})
    transitions = transitions.merge(baseline_prediction, on=["frame_id", "model"], validate="many_to_one")
    crossing_types = [("detected_to_missed", 1, 1, 0), ("missed_to_detected", 1, 0, 1), ("legit_to_FP", 0, 0, 1), ("FP_to_legit", 0, 1, 0)]
    crossing_rows = []
    for model in MODELS:
        for condition in conditions:
            for kind, truth, before, after in crossing_types:
                group = transitions[(transitions.model == model) & (transitions.condition == condition) & (transitions.true_label == truth)]
                eligible = group[group.baseline_prediction == before]
                count = int((eligible.prediction == after).sum())
                crossing_rows.append(dict(model=model, condition=condition, transition_type=kind, true_label=truth, baseline_prediction=before, condition_prediction=after, count=count, N=len(group), eligible_N=len(eligible), rate=count / len(eligible) if len(eligible) else np.nan))
    table = pd.DataFrame(crossing_rows)
    def draw_transitions(ax):
        pivot = table.pivot(index=["model", "condition"], columns="transition_type", values="count")
        pivot.plot.bar(stacked=True, ax=ax, width=.85, rot=65)
        labels = []
        for model, condition in pivot.index:
            subset = table[(table.model == model) & (table.condition == condition)]
            labels.append(f"{model}, {condition}\nNph={subset[subset.true_label == 1].N.iloc[0]}, Nleg={subset[subset.true_label == 0].N.iloc[0]}")
        ax.set_xticklabels(labels, rotation=65, fontsize=7)
        ax.legend(title="Class-specific crossing", fontsize=8)
    save("08_threshold_transitions", "Four threshold-transition types", "Which paired predictions cross the detector threshold?", table, draw_transitions,
         "Model, condition (class denominators shown)", "Crossing count", "Four class-specific crossings are counted: detected→missed and missed→detected for phishing; legitimate→false-positive and false-positive→legitimate for legitimate messages. Unchanged predictions are excluded.", "N is the class denominator; eligible_N is the baseline state at risk of each crossing; absent-class rates remain unavailable.", "Do not combine phishing misses and legitimate false positives as a single evasion measure.")

    nonbaseline = data[data.condition != "C0"]
    frame_movement = nonbaseline.groupby("frame_id").absolute_delta.mean().sort_values(kind="stable")
    available_nonbaseline = available[available.condition != "C0"]
    for slug, title, candidates in [("09_representative_frame", "Representative complete frame (nearest median mean absolute movement)", nonbaseline), ("10_extreme_case", "EXTREME CASE—NOT REPRESENTATIVE", available_nonbaseline)]:
        is_representative = slug.startswith("09")
        selection_filter = "primary_complete_case == True" if is_representative else "all approved available pairs with recorded predictions, including incomplete frames"
        if candidates.empty:
            save(slug, title + ": unavailable", "Is a paired frame available to illustrate?", candidates.copy(), lambda ax: ax.text(.5, .5, "Example unavailable: no eligible pair", transform=ax.transAxes, ha="center"), "Condition", "Phishing probability", "No eligible nonbaseline pair is available for example selection.", "An unavailable example must remain unavailable.", "Do not substitute a frame outside the stated selection cohort.", filters=selection_filter)
            continue
        if is_representative:
            median = frame_movement.median()
            frame = (frame_movement - median).abs().sort_values(kind="stable").index[0]
            example = data[data.frame_id == frame].copy()
            observation = f"Frame {frame}; mean absolute movement across models and non-C0 conditions = {frame_movement.loc[frame]:.4f}, closest to complete-cohort median {median:.4f}."
            selected_model, selected_condition = "all", "all"
        else:
            extreme_row = candidates.sort_values(["absolute_delta", "frame_id", "condition", "model"], ascending=[False, True, True, True], kind="stable").iloc[0]
            frame = extreme_row.frame_id
            example = available[available.frame_id == frame].copy()
            selected_model, selected_condition = extreme_row.model, extreme_row.condition
            observation = f"Strongest single pair among all approved available pairs: frame {frame}, {selected_model}, {selected_condition}, |Δ|={extreme_row.absolute_delta:.4f}; frame complete-case membership={bool(extreme_row.primary_complete_case)}. EXTREME CASE—NOT REPRESENTATIVE."
        example["selection_mean_absolute_delta"] = float(candidates[candidates.frame_id == frame].absolute_delta.mean())
        example["selected_model"] = selected_model
        example["selected_condition"] = selected_condition
        example["threshold"] = .5
        originals = matrix[matrix.condition == "C0"].set_index("frame_id").text
        example["before_text"] = example.frame_id.map(originals)
        example["after_text"] = example.text
        def draw_example(ax, t=example):
            for model in MODELS:
                rows = t[t.model == model].set_index("condition").reindex(conditions)
                ax.plot(conditions, rows.probability, marker="o", label=model)
            ax.axhline(.5, color="grey", ls="--", label="Frozen threshold = 0.5")
            ax.set_ylim(0, 1)
            ax.tick_params(axis="x", rotation=20)
            ax.legend(fontsize=8)
        detail = "\n".join(f"- {r.condition} (true_label={r.true_label}): {r.after_text}" for r in example.drop_duplicates("condition").itertuples())
        scores = "\n".join(f"- {r.model}, {r.condition}: P0={r.C0_probability:.8f}, Pi={r.probability:.8f}, P0−Pi={r.signed_delta:.8f}, prediction={r.prediction}" for r in example.itertuples())
        save(slug, title, "What does a concrete paired frame look like?", example, draw_example, "Condition", "Phishing probability", observation,
             "This illustrates the stated selection rule; exact before/after text, model probabilities, true labels, and the frozen threshold are exported.", "A single frame cannot establish overall model performance or population effects.", filters=selection_filter)
        catalog[-1] += f"\nBefore text:\n\n{example.before_text.iloc[0]}\n\nCondition texts:\n\n{detail}\n\nModel probabilities:\n\n{scores}\n"

    manip = matrix[matrix.condition != "C0"][["frame_id", "condition"]].merge(distances, on=["frame_id", "condition"], how="left", validate="one_to_one")
    manipulation_filter = "all approved available non-C0 rewrites; manipulation check independent of primary complete-case eligibility"
    metrics = [c for c in ["token_jaccard", "normalized_edit_distance", "frozen_tfidf_cosine_similarity", "surface_distance"] if c in manip]
    long = manip.melt(id_vars=["frame_id", "condition"], value_vars=metrics, var_name="metric", value_name="value")
    summary = long.groupby(["condition", "metric"], sort=True).value.agg(["count", "median", "min", "max"]).reset_index()
    long = long.merge(summary.rename(columns={"count": "observed_N", "median": "group_median", "min": "group_min", "max": "group_max"}), on=["condition", "metric"])
    def draw_distances(ax):
        groups = list(long.groupby(["condition", "metric"], sort=True))
        observed = [(name, g.value.dropna()) for name, g in groups if g.value.notna().any()]
        if observed:
            label_parameter = "tick_labels" if "tick_labels" in inspect.signature(ax.boxplot).parameters else "labels"
            ax.boxplot([g.to_numpy() for _, g in observed], **{label_parameter: [f"{c}\n{m}" for (c, m), _ in observed]}, showfliers=True)
            ax.tick_params(axis="x", rotation=65, labelsize=7)
        else:
            ax.text(.5, .5, "No observed manipulation distances", transform=ax.transAxes, ha="center")
    save("M1_distance_distributions", "Manipulation-check distance distributions", "How much surface variation did each condition produce?", long, draw_distances,
         "Condition and distance measure", "Observed distance / similarity", "Distributions retain each metric's definition; unavailable values are omitted and observed N is exported.",
         "TF-IDF cosine is lexical feature similarity; Jaccard and edit measures describe surface changes.", "Lexical cosine similarity must not be described as semantic preservation.", filters=manipulation_filter, extra_sources=[str(distance_path.relative_to(root))])

    semantic_col = "semantic_similarity_if_available"
    has_semantic = semantic_col in manip and pd.to_numeric(manip[semantic_col], errors="coerce").notna().any()
    semantic = manip.copy()
    if has_semantic:
        semantic["plotted_y"] = pd.to_numeric(semantic[semantic_col], errors="coerce")
        ylabel = "Available semantic similarity (recorded metric)"
        observation = f"{semantic.plotted_y.notna().sum()} variants have a recorded semantic similarity; absent scores are omitted."
    else:
        semantic["plotted_y"] = semantic.semantic_preserved.map(lambda v: np.nan if pd.isna(v) else float(str(v).lower() in ["true", "1", "1.0", "yes"]))
        ylabel = "Reviewed semantic preservation (0=no, 1=yes)"
        observation = "Semantic similarity scores are unavailable. This plot uses reviewed preservation decisions as a binary outcome, without inventing semantic scores."
    def draw_semantic(ax):
        for condition, group in semantic.groupby("condition"):
            rows = group.dropna(subset=["surface_distance", "plotted_y"])
            ax.scatter(rows.surface_distance, rows.plotted_y, s=20, alpha=.45, label=condition)
        if not has_semantic:
            ax.set_yticks([0, 1], ["Not preserved", "Preserved"])
            ax.set_ylim(-.15, 1.3)
            ax.text(.02, .95, "Semantic scores unavailable; reviewed binary decisions", va="top", transform=ax.transAxes, fontsize=9)
        ax.legend(fontsize=8)
    save("M2_semantic_preservation", "Semantic preservation versus surface distance", "Were meanings preserved across the observed surface changes?", semantic, draw_semantic,
         "Surface distance", ylabel, observation, "Reviewed binary decisions and recorded similarity scores are distinct evidence types.",
         "Neither lexical cosine nor missing semantic scores are evidence of semantic equivalence.", filters=manipulation_filter, extra_sources=[str(distance_path.relative_to(root))])

    _write(root / "results/benchmark_v3_2/FIGURE_CATALOG.md", ("# v3.2 figure catalog\n\nMain detector comparisons use primary complete frames. The extreme example and manipulation checks use all approved available pairs. When no complete frames exist, graph 07 explicitly shows exploratory available-pair association. Intervals resample frames, not model-condition rows. No missing outcome is replaced with zero.\n\n" + "\n".join(catalog)).encode("utf-8"))
    _write(root / "results/benchmark_v3_2/PRESENTATION_GRAPH_NOTES.md", ("# Presentation graph notes\n\nRead each note alongside its graph and exact-data CSV. Allow approximately 20–40 seconds per figure.\n\n" + "\n".join(notes)).encode("utf-8"))
    return outputs


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path("."))
    parser.add_argument("--bootstrap-draws", type=int, default=2000)
    args = parser.parse_args()
    generate(args.root, bootstrap_draws=args.bootstrap_draws)


if __name__ == "__main__":
    main()
