"""Build an offline, read-only dashboard for the paired rewrite experiment."""

from __future__ import annotations

import argparse
import hashlib
import html
from pathlib import Path
from typing import Iterable

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


DEFAULT_PAIRS = Path("data/rewrite_experiment/rewrite_pairs.csv")
DEFAULT_RESULTS = Path("results/rewrite_experiment")
DEFAULT_OUTPUT = DEFAULT_RESULTS / "dashboard"
ORIGINAL = "T0_original"
REWRITE = "T1_llm_neutral_rewrite"
MODEL_LABELS = {
    "tfidf_logistic_regression": "TF-IDF + Logistic Regression",
    "tfidf_random_forest": "TF-IDF + Random Forest",
}
MODEL_COLORS = {
    "tfidf_logistic_regression": "#2563eb",
    "tfidf_random_forest": "#7c3aed",
}
METRICS = [
    ("accuracy", "Accuracy"), ("precision", "Precision"), ("recall", "Recall"),
    ("f1", "F1"), ("false_negative_rate", "False-negative rate"),
    ("specificity", "Specificity"), ("false_positive_rate", "False-positive rate"),
    ("balanced_accuracy", "Balanced accuracy"),
    ("mean_phishing_probability", "Mean phishing probability"),
]


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def read_optional_csv(path: Path) -> pd.DataFrame:
    if not path.exists() or path.stat().st_size == 0:
        return pd.DataFrame()
    try:
        return pd.read_csv(path, keep_default_na=False)
    except (pd.errors.EmptyDataError, pd.errors.ParserError):
        return pd.DataFrame()


def numeric(series: pd.Series) -> pd.Series:
    return pd.to_numeric(series, errors="coerce")


def compute_progress(pairs: pd.DataFrame) -> dict[str, int]:
    required = {"pair_id", "condition", "generation_status", "human_review_status"}
    missing = sorted(required.difference(pairs.columns))
    if missing:
        raise ValueError(f"rewrite_pairs.csv is missing columns: {missing}")
    originals = pairs[pairs["condition"].eq(ORIGINAL)]
    rewrites = pairs[pairs["condition"].eq(REWRITE)]
    if originals["pair_id"].duplicated().any() or rewrites["pair_id"].duplicated().any():
        raise ValueError("Duplicate pair_id/condition rows found")
    if set(originals["pair_id"]) != set(rewrites["pair_id"]):
        raise ValueError("Original and rewrite pair_id sets do not match")
    status = rewrites["generation_status"].astype(str).str.lower()
    completed = int(status.eq("completed").sum())
    rejected = int(status.str.contains("reject", regex=False).sum())
    pending = int(len(rewrites) - completed - rejected)
    approved = int(
        rewrites["human_review_status"].astype(str).str.lower().eq("approved").sum()
    )
    return {
        "total_pairs": int(len(originals)), "completed": completed,
        "pending": pending, "rejected": rejected, "approved": approved,
    }


def safe_text(value: object, limit: int = 240) -> str:
    text = str(value or "").replace("https://", "hxxps://").replace("http://", "hxxp://")
    if len(text) > limit:
        text = text[: limit - 1] + "…"
    return html.escape(text)


def display_value(value: object, percent: bool = False) -> str:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return "N/A"
    if not np.isfinite(number):
        return "N/A"
    return f"{number:.1%}" if percent else f"{number:.4f}"


def save_figure(fig: plt.Figure, path: Path) -> None:
    fig.savefig(path, dpi=180, bbox_inches="tight", facecolor="white")
    plt.close(fig)


def progress_figure(progress: dict[str, int], path: Path) -> None:
    labels = ["Completed", "Pending", "Rejected"]
    values = [progress["completed"], progress["pending"], progress["rejected"]]
    colors = ["#16a34a", "#f59e0b", "#dc2626"]
    total = max(progress["total_pairs"], 1)
    fig, ax = plt.subplots(figsize=(11, 2.2))
    left = 0
    for label, value, color in zip(labels, values, colors):
        ax.barh([0], [value], left=left, color=color, height=0.45, label=label)
        if value:
            if value / total < 0.06:
                ax.text(min(left + value, total) - 0.25, 0.34, f"{value} ({value / total:.1%})",
                        ha="right", va="center", color=color, fontweight="bold")
            else:
                ax.text(left + value / 2, 0, f"{value}\n{value / total:.1%}", ha="center", va="center",
                        color="white" if label != "Pending" else "#111827", fontweight="bold")
        left += value
    ax.set_xlim(0, total)
    ax.set_ylim(-0.35, 0.55)
    ax.set_yticks([])
    ax.set_xlabel("Rewrite pairs")
    ax.set_title("Generation progress", loc="left", fontweight="bold")
    ax.legend(ncol=3, frameon=False, loc="upper center", bbox_to_anchor=(0.5, -0.28))
    ax.spines[["top", "right", "left"]].set_visible(False)
    save_figure(fig, path)


def performance_figure(metrics: pd.DataFrame, path: Path) -> bool:
    if metrics.empty or not {"model", "condition"}.issubset(metrics.columns):
        return False
    models = [model for model in MODEL_LABELS if model in set(metrics["model"])]
    if not models:
        models = list(dict.fromkeys(metrics["model"].astype(str)))
    fig, axes = plt.subplots(3, 3, figsize=(14, 11), sharey=True)
    for ax, (column, title) in zip(axes.flat, METRICS):
        x = np.arange(len(models), dtype=float)
        width = 0.34
        for offset, condition, alpha, hatch in (
            (-width / 2, ORIGINAL, 0.95, ""), (width / 2, REWRITE, 0.55, "//")
        ):
            heights: list[float] = []
            for model in models:
                rows = metrics[(metrics["model"].eq(model)) & (metrics["condition"].eq(condition))]
                value = numeric(rows[column]).iloc[0] if column in rows and len(rows) else np.nan
                heights.append(float(value) if pd.notna(value) else np.nan)
            bars = ax.bar(
                x + offset, np.nan_to_num(heights, nan=0.0), width,
                color=[MODEL_COLORS.get(model, "#64748b") for model in models],
                alpha=alpha, hatch=hatch, edgecolor="white", linewidth=0.7,
                label="Original" if condition == ORIGINAL else "Rewrite",
            )
            for bar, value in zip(bars, heights):
                if np.isnan(value):
                    ax.text(bar.get_x() + bar.get_width() / 2, 0.025, "N/A", rotation=90,
                            ha="center", va="bottom", fontsize=8, color="#64748b")
                else:
                    ax.text(bar.get_x() + bar.get_width() / 2, min(value + 0.025, 1.04),
                            f"{value:.2f}", ha="center", va="bottom", fontsize=7)
        ax.set_title(title, fontsize=10, fontweight="bold")
        ax.set_ylim(0, 1.1)
        ax.set_xticks(x, [MODEL_LABELS.get(model, model).replace("TF-IDF + ", "") for model in models],
                      rotation=12, ha="right", fontsize=8)
        ax.grid(axis="y", alpha=0.2)
        ax.spines[["top", "right"]].set_visible(False)
    handles = [
        plt.Rectangle((0, 0), 1, 1, color="#475569", alpha=0.95, label="Original"),
        plt.Rectangle((0, 0), 1, 1, color="#475569", alpha=0.55, hatch="//", label="Rewrite"),
    ]
    fig.legend(handles=handles, loc="lower center", ncol=2, frameon=False)
    fig.suptitle("Original versus rewritten detector performance", x=0.04, ha="left",
                 fontsize=15, fontweight="bold")
    fig.tight_layout(rect=(0, 0.04, 1, 0.96))
    save_figure(fig, path)
    return True


def paired_predictions(predictions: pd.DataFrame) -> pd.DataFrame:
    required = {"model", "pair_id", "condition", "binary_label", "predicted_binary_label", "phishing_probability"}
    if predictions.empty or not required.issubset(predictions.columns):
        return pd.DataFrame()
    if predictions.duplicated(["model", "pair_id", "condition"]).any():
        return pd.DataFrame()
    original = predictions[predictions["condition"].eq(ORIGINAL)].copy()
    rewrite = predictions[predictions["condition"].eq(REWRITE)].copy()
    before = original.rename(columns={
        "predicted_binary_label": "prediction_original",
        "phishing_probability": "probability_original",
        "text": "text_original",
    })
    after = rewrite[[column for column in rewrite.columns if column in {
        "model", "pair_id", "predicted_binary_label", "phishing_probability", "text"
    }]].rename(columns={
        "predicted_binary_label": "prediction_rewrite",
        "phishing_probability": "probability_rewrite",
        "text": "text_rewrite",
    })
    merged = before.merge(after, on=["model", "pair_id"], how="inner", validate="one_to_one")
    for column in ("binary_label", "prediction_original", "prediction_rewrite",
                   "probability_original", "probability_rewrite"):
        merged[column] = numeric(merged[column])
    merged["confidence_drop"] = merged["probability_original"] - merged["probability_rewrite"]
    merged["prediction_changed"] = merged["prediction_original"].ne(merged["prediction_rewrite"])
    return merged


def confusion_figure(predictions: pd.DataFrame, path: Path) -> bool:
    if predictions.empty or not {"model", "condition", "binary_label", "predicted_binary_label"}.issubset(predictions.columns):
        return False
    panels = [(model, condition) for model in MODEL_LABELS for condition in (ORIGINAL, REWRITE)]
    available = [(m, c) for m, c in panels if ((predictions["model"].eq(m)) & (predictions["condition"].eq(c))).any()]
    if not available:
        return False
    matrices = []
    for model, condition in available:
        subset = predictions[(predictions["model"].eq(model)) & (predictions["condition"].eq(condition))]
        table = pd.crosstab(numeric(subset["binary_label"]), numeric(subset["predicted_binary_label"]))
        matrices.append(table.reindex(index=[0, 1], columns=[0, 1], fill_value=0).to_numpy())
    vmax = max(int(matrix.max()) for matrix in matrices) or 1
    fig, axes = plt.subplots(2, 2, figsize=(10, 8))
    for ax in axes.flat:
        ax.axis("off")
    for ax, (model, condition), matrix in zip(axes.flat, available, matrices):
        ax.axis("on")
        image = ax.imshow(matrix, cmap="Blues", vmin=0, vmax=vmax)
        for row in range(2):
            for column in range(2):
                ax.text(column, row, str(matrix[row, column]), ha="center", va="center",
                        color="white" if matrix[row, column] > vmax / 2 else "#111827", fontweight="bold")
        ax.set_xticks([0, 1], ["Non-phishing", "Phishing"])
        ax.set_yticks([0, 1], ["Non-phishing", "Phishing"])
        ax.set_xlabel("Predicted")
        ax.set_ylabel("True")
        ax.set_title(f"{MODEL_LABELS.get(model, model)}\n{'Original' if condition == ORIGINAL else 'Rewrite'}",
                     fontsize=10, fontweight="bold")
    fig.colorbar(image, ax=axes.ravel().tolist(), shrink=0.75, label="Rows")
    fig.suptitle("Confusion matrices (shared color scale)", x=0.08, ha="left", fontweight="bold")
    save_figure(fig, path)
    return True


def transition_figure(transitions: pd.DataFrame, path: Path) -> bool:
    required = {"model", "prediction_original", "prediction_rewrite", "rows"}
    if transitions.empty or not required.issubset(transitions.columns):
        return False
    if "true_label" in transitions.columns:
        transitions = transitions[transitions["true_label"].astype(str).str.lower().eq("phishing")]
    mapping = [
        (1, 1, "Detected → detected", "#16a34a"),
        (1, 0, "Detected → missed", "#dc2626"),
        (0, 1, "Missed → detected", "#2563eb"),
        (0, 0, "Missed → missed", "#64748b"),
    ]
    models = [model for model in MODEL_LABELS if model in set(transitions["model"])]
    if not models:
        return False
    fig, ax = plt.subplots(figsize=(10, 4.8))
    x = np.arange(len(models))
    bottom = np.zeros(len(models))
    for before, after, label, color in mapping:
        values = []
        for model in models:
            rows = transitions[
                transitions["model"].eq(model)
                & numeric(transitions["prediction_original"]).eq(before)
                & numeric(transitions["prediction_rewrite"]).eq(after)
            ]
            values.append(int(numeric(rows["rows"]).sum()) if len(rows) else 0)
        bars = ax.bar(x, values, bottom=bottom, color=color, label=label)
        for bar, value, base in zip(bars, values, bottom):
            if value:
                ax.text(bar.get_x() + bar.get_width() / 2, base + value / 2, str(value),
                        ha="center", va="center", color="white", fontweight="bold")
        bottom += np.asarray(values)
    ax.set_xticks(x, [MODEL_LABELS[model] for model in models])
    ax.set_ylabel("Phishing pairs")
    ax.set_title("Paired prediction transitions", loc="left", fontweight="bold")
    ax.legend(frameon=False, ncol=2, loc="upper center", bbox_to_anchor=(0.5, -0.12))
    ax.spines[["top", "right"]].set_visible(False)
    fig.tight_layout(rect=(0, 0.12, 1, 1))
    save_figure(fig, path)
    return True


def confidence_figures(paired: pd.DataFrame, figures: Path) -> list[str]:
    if paired.empty:
        return []
    # The confirmatory rewrite estimand is phishing recall. Keep the confidence
    # display on the same phishing-pair population; legitimate controls are
    # reported separately through specificity and false-positive rate.
    paired = paired[numeric(paired["binary_label"]).eq(1)].copy()
    if paired.empty:
        return []
    models = [model for model in MODEL_LABELS if model in set(paired["model"])]
    if not models:
        return []
    fig, axes = plt.subplots(1, len(models), figsize=(6 * len(models), 4), squeeze=False)
    for ax, model in zip(axes.flat, models):
        values = paired.loc[paired["model"].eq(model), "confidence_drop"].dropna()
        ax.hist(values, bins=min(15, max(5, len(values) // 3)), color=MODEL_COLORS[model], alpha=0.8,
                edgecolor="white")
        ax.axvline(0, color="#111827", linewidth=1)
        if len(values):
            ax.axvline(values.mean(), color="#dc2626", linestyle="--", label=f"Mean {values.mean():.4f}")
        ax.set_title(MODEL_LABELS[model], fontsize=10, fontweight="bold")
        ax.set_xlabel("Original probability − rewrite probability")
        ax.set_ylabel("Pairs")
        ax.legend(frameon=False)
    fig.suptitle("Phishing pairs: distribution of probability change", x=0.05, ha="left", fontweight="bold")
    histogram = figures / "confidence_drop_histograms.png"
    save_figure(fig, histogram)

    fig, axes = plt.subplots(1, len(models), figsize=(6 * len(models), 5), squeeze=False)
    for ax, model in zip(axes.flat, models):
        subset = paired[paired["model"].eq(model)]
        ax.scatter(subset["probability_original"], subset["probability_rewrite"],
                   color=MODEL_COLORS[model], alpha=0.72, edgecolor="white")
        ax.plot([0, 1], [0, 1], color="#64748b", linestyle="--", linewidth=1)
        ax.set_xlim(0, 1)
        ax.set_ylim(0, 1)
        ax.set_aspect("equal", adjustable="box")
        ax.set_xlabel("Original phishing probability")
        ax.set_ylabel("Rewrite phishing probability")
        ax.set_title(MODEL_LABELS[model], fontsize=10, fontweight="bold")
        ax.grid(alpha=0.2)
    fig.suptitle("Phishing pairs: original-versus-rewrite probabilities", x=0.05, ha="left", fontweight="bold")
    scatter = figures / "confidence_scatter.png"
    save_figure(fig, scatter)
    return [histogram.name, scatter.name]


def html_table(frame: pd.DataFrame, columns: Iterable[tuple[str, str]], limit: int = 12) -> str:
    columns = [(column, label) for column, label in columns if column in frame.columns]
    if frame.empty or not columns:
        return '<p class="na">N/A — no eligible rows are available.</p>'
    header = "".join(f"<th>{html.escape(label)}</th>" for _, label in columns)
    body = []
    for _, row in frame.head(limit).iterrows():
        body.append("<tr>" + "".join(f"<td>{safe_text(row[column])}</td>" for column, _ in columns) + "</tr>")
    return f'<div class="table-wrap"><table><thead><tr>{header}</tr></thead><tbody>{"".join(body)}</tbody></table></div>'


def interpretation(metrics: pd.DataFrame, statistics: pd.DataFrame) -> list[str]:
    statements: list[str] = []
    if statistics.empty:
        return ["Evaluation statistics are not available yet; no detector-performance conclusion is drawn."]
    for _, row in statistics.iterrows():
        model = MODEL_LABELS.get(str(row.get("model", "")), str(row.get("model", "Model")))
        original_recall = pd.to_numeric(pd.Series([row.get("original_recall")]), errors="coerce").iloc[0]
        rewrite_recall = pd.to_numeric(pd.Series([row.get("rewrite_recall")]), errors="coerce").iloc[0]
        p_value = pd.to_numeric(pd.Series([row.get("mcnemar_exact_p_value")]), errors="coerce").iloc[0]
        ci_low = pd.to_numeric(pd.Series([row.get("confidence_drop_ci95_low")]), errors="coerce").iloc[0]
        ci_high = pd.to_numeric(pd.Series([row.get("confidence_drop_ci95_high")]), errors="coerce").iloc[0]
        mean_drop = pd.to_numeric(pd.Series([row.get("mean_confidence_drop")]), errors="coerce").iloc[0]
        if pd.notna(original_recall) and pd.notna(rewrite_recall):
            if rewrite_recall >= original_recall:
                statements.append(f"{model}: the evaluated pairs provide no evidence that neutral rewriting reduced recall.")
            else:
                statements.append(f"{model}: recall was lower after rewriting by {original_recall - rewrite_recall:.1%} in the evaluated pairs.")
        if pd.notna(mean_drop) and abs(mean_drop) > 0 and pd.notna(ci_low) and pd.notna(ci_high):
            if ci_low <= 0 <= ci_high:
                statements.append(f"{model}: mean confidence changed, but its 95% bootstrap interval includes zero; the estimate is inconclusive.")
            else:
                statements.append(f"{model}: the bootstrap interval excludes zero for the recorded mean confidence change.")
        if pd.notna(p_value):
            statements.append(
                f"{model}: McNemar p={p_value:.4f}; "
                + ("the paired prediction difference meets the 0.05 threshold." if p_value < 0.05
                   else "the paired prediction difference is not statistically significant at α=0.05.")
            )
    if not metrics.empty and {"condition", "specificity", "model"}.issubset(metrics.columns):
        for _, row in metrics[metrics["condition"].eq(REWRITE)].iterrows():
            value = pd.to_numeric(pd.Series([row["specificity"]]), errors="coerce").iloc[0]
            if pd.notna(value) and value < 0.5:
                model = MODEL_LABELS.get(str(row["model"]), str(row["model"]))
                statements.append(f"{model}: low specificity indicates a separate false-positive weakness on legitimate banking controls.")
    return statements


def build_dashboard(pairs_path: Path, results_dir: Path, output_dir: Path) -> Path:
    source_hash = file_sha256(pairs_path)
    pairs = pd.read_csv(pairs_path, keep_default_na=False)
    progress = compute_progress(pairs)
    originals = pairs[pairs["condition"].eq(ORIGINAL)].copy()
    rewrites = pairs[pairs["condition"].eq(REWRITE)].copy()
    output_dir.mkdir(parents=True, exist_ok=True)
    figures = output_dir / "figures"
    figures.mkdir(parents=True, exist_ok=True)

    metrics = read_optional_csv(results_dir / "metrics_by_model_and_condition.csv")
    predictions = read_optional_csv(results_dir / "paired_predictions.csv")
    transitions = read_optional_csv(results_dir / "paired_transition_table.csv")
    statistics = read_optional_csv(results_dir / "statistical_tests.csv")
    false_negatives = read_optional_csv(results_dir / "false_negatives_after_rewrite.csv")
    paired = paired_predictions(predictions)

    progress_figure(progress, figures / "generation_progress.png")
    has_performance = performance_figure(metrics, figures / "detector_performance.png")
    has_confusion = confusion_figure(predictions, figures / "confusion_matrices.png")
    has_transitions = transition_figure(transitions, figures / "paired_transitions.png")
    confidence_images = confidence_figures(paired, figures)

    label_counts = numeric(originals.get("binary_label", pd.Series(dtype=float))).value_counts()
    source_counts = originals.get("source_dataset", pd.Series(dtype=str)).value_counts()
    generator_values = sorted(
        value for value in rewrites.get("generator_model", pd.Series(dtype=str)).astype(str).unique()
        if value and value.lower() not in {"nan", "not_applicable"}
    )
    generator = ", ".join(generator_values) if generator_values else "N/A"
    model_files = sorted(Path("models/final").glob("*.joblib"))
    detected_models = {path.stem for path in model_files} | set(metrics.get("model", pd.Series(dtype=str)))
    primary = MODEL_LABELS["tfidf_logistic_regression"] if "tfidf_logistic_regression" in detected_models else "N/A"
    comparison = MODEL_LABELS["tfidf_random_forest"] if "tfidf_random_forest" in detected_models else "N/A"
    evaluated_pairs = int(predictions["pair_id"].nunique()) if "pair_id" in predictions else 0
    review_note = "Exploratory evaluation; human review is pending." if progress["approved"] < evaluated_pairs else "Approved-review evaluation."

    cards = [
        ("Total pairs", progress["total_pairs"]), ("Completed rewrites", progress["completed"]),
        ("Pending rewrites", progress["pending"]), ("Rejected rewrites", progress["rejected"]),
        ("Approved reviews", progress["approved"]), ("Phishing", int(label_counts.get(1, 0))),
        ("Non-phishing", int(label_counts.get(0, 0))), ("SmishTank", int(source_counts.get("SmishTank", 0))),
        ("SmishX", int(source_counts.get("SmishX", 0))), ("Generator", generator),
        ("Primary detector", primary), ("Comparison detector", comparison),
    ]
    card_html = "".join(
        f'<div class="card"><span>{html.escape(label)}</span><strong>{safe_text(value, 100)}</strong></div>'
        for label, value in cards
    )

    rejected = rewrites[rewrites["generation_status"].astype(str).str.contains("reject", case=False, regex=False)]
    false_positives = predictions[
        numeric(predictions.get("binary_label", pd.Series(index=predictions.index))).eq(0)
        & numeric(predictions.get("predicted_binary_label", pd.Series(index=predictions.index))).eq(1)
    ] if not predictions.empty else pd.DataFrame()
    largest = paired.sort_values("confidence_drop", ascending=False) if not paired.empty else pd.DataFrame()
    changed = paired[paired["prediction_changed"]] if not paired.empty else pd.DataFrame()

    stats_table = html_table(statistics, [
        ("model", "Model"), ("phishing_pairs", "Pairs"), ("original_recall", "Original recall"),
        ("rewrite_recall", "Rewrite recall"), ("recall_drop", "Recall drop"),
        ("original_fnr", "Original FNR"), ("rewrite_fnr", "Rewrite FNR"),
        ("originally_detected", "Originally detected"), ("became_false_negative", "Became FN"),
        ("attack_success_rate", "ASR"), ("mean_confidence_drop", "Mean confidence drop"),
        ("confidence_drop_ci95_low", "CI low"), ("confidence_drop_ci95_high", "CI high"),
        ("mcnemar_exact_p_value", "McNemar p"),
    ])
    statements = "".join(f"<li>{html.escape(text)}</li>" for text in interpretation(metrics, statistics))

    optional_performance = '<img src="figures/detector_performance.png" alt="Detector performance comparison">' if has_performance else '<p class="na">N/A — evaluation metrics are not available.</p>'
    optional_confusion = '<img src="figures/confusion_matrices.png" alt="Confusion matrices">' if has_confusion else '<p class="na">N/A — paired predictions are not available.</p>'
    optional_transitions = '<img src="figures/paired_transitions.png" alt="Paired prediction transitions">' if has_transitions else '<p class="na">N/A — paired transition data are not available.</p>'
    optional_confidence = "".join(f'<img src="figures/{name}" alt="Confidence analysis">' for name in confidence_images) or '<p class="na">N/A — paired probabilities are not available.</p>'

    document = f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Banking Smishing Rewrite Robustness Dashboard</title>
<style>
:root{{--ink:#172033;--muted:#64748b;--line:#dbe3ee;--panel:#fff;--bg:#f5f7fa;--blue:#2563eb;--purple:#7c3aed;--green:#16a34a;--amber:#f59e0b;--red:#dc2626}}
*{{box-sizing:border-box}} body{{margin:0;background:var(--bg);color:var(--ink);font:15px/1.55 Inter,Segoe UI,Arial,sans-serif}} main{{max-width:1280px;margin:auto;padding:36px 28px 64px}}
h1{{font-size:32px;margin:0 0 6px}} h2{{font-size:21px;margin:0 0 18px}} h3{{font-size:16px;margin:22px 0 10px}} .subtitle,.meta,.na{{color:var(--muted)}}
section{{background:var(--panel);border:1px solid var(--line);border-radius:14px;padding:24px;margin:20px 0;box-shadow:0 2px 10px #0f172a0a}}
.cards{{display:grid;grid-template-columns:repeat(auto-fit,minmax(175px,1fr));gap:12px}} .card{{border:1px solid var(--line);border-radius:10px;padding:14px;background:#fbfcfe}} .card span{{display:block;color:var(--muted);font-size:12px;text-transform:uppercase;letter-spacing:.04em}} .card strong{{display:block;font-size:19px;margin-top:5px;overflow-wrap:anywhere}}
img{{display:block;max-width:100%;height:auto;margin:14px auto}} .pipeline{{display:grid;gap:7px;max-width:680px;margin:auto;text-align:center}} .node{{padding:10px 14px;border:1px solid #bfd0e8;border-radius:9px;background:#f8fbff;font-weight:600}} .arrow{{color:var(--blue);font-size:20px}}
.principles{{display:grid;grid-template-columns:repeat(auto-fit,minmax(250px,1fr));gap:8px;margin-top:20px}} .principles div{{border-left:4px solid var(--blue);padding:7px 10px;background:#f8fafc}}
.notice{{border-left:5px solid var(--amber);padding:12px 15px;background:#fffbeb;margin:14px 0}} .interpretation{{border-left:5px solid var(--purple);background:#faf5ff}}
.table-wrap{{overflow-x:auto}} table{{width:100%;border-collapse:collapse;font-size:13px}} th,td{{padding:9px;border-bottom:1px solid var(--line);text-align:left;vertical-align:top}} th{{background:#f1f5f9;position:sticky;top:0}} td{{max-width:360px;overflow-wrap:anywhere}}
.two{{display:grid;grid-template-columns:repeat(auto-fit,minmax(420px,1fr));gap:18px}} footer{{color:var(--muted);font-size:12px;margin-top:25px}}
@media(max-width:600px){{main{{padding:22px 12px}}.two{{grid-template-columns:1fr}}}}
</style></head><body><main>
<header><h1>Banking Smishing Rewrite Robustness</h1><p class="subtitle">Offline reproducible dashboard · SmishX + SmishTank · neutral paired LLM rewriting</p><p class="meta">Evaluation coverage: {evaluated_pairs} unique pair(s). {html.escape(review_note)}</p></header>
<section><h2>1. Experiment overview</h2><div class="cards">{card_html}</div></section>
<section><h2>2. Generation progress</h2><img src="figures/generation_progress.png" alt="Generation progress"></section>
<section><h2>3. Experimental pipeline</h2><div class="pipeline">
<div class="node">SmishX + SmishTank</div><div class="arrow">↓</div><div class="node">Final leakage-controlled banking SMS dataset</div><div class="arrow">↓</div><div class="node">Frozen original banking test set</div><div class="arrow">↓</div><div class="node">Neutral LLM rewriting</div><div class="arrow">↓</div><div class="node">Automated safety validation</div><div class="arrow">↓</div><div class="node">Human semantic review</div><div class="arrow">↓</div><div class="node">Frozen Logistic Regression and Random Forest</div><div class="arrow">↓</div><div class="node">Paired robustness evaluation</div></div>
<div class="principles"><div>Detectors are not retrained.</div><div>Detector outputs are not provided to the LLM.</div><div>Original and rewrite share the same pair_id.</div><div>URLs remain defanged.</div><div>No prompt optimization uses detector feedback.</div></div></section>
<section><h2>4. Original versus rewritten detector performance</h2><div class="notice">Metrics are displayed exactly as recorded. Missing specificity-dependent values remain N/A. Current results may be exploratory until human review is complete.</div>{optional_performance}</section>
<section><h2>5. Confusion matrices</h2>{optional_confusion}</section>
<section><h2>6. Paired prediction transitions</h2><p>Transitions are reported neutrally. “Detected → missed” identifies an originally detected phishing row that becomes a false negative after rewriting.</p>{optional_transitions}</section>
<section><h2>7. Confidence changes</h2><p><code>confidence_drop = original phishing probability − rewritten phishing probability</code></p>{optional_confidence}
<h3>Largest recorded confidence drops</h3>{html_table(largest, [("model","Model"),("pair_id","Pair"),("confidence_drop","Drop"),("probability_original","Original probability"),("probability_rewrite","Rewrite probability"),("text_original","Original"),("text_rewrite","Rewrite")])}</section>
<section><h2>8. Statistical results</h2>{stats_table}<p class="meta">Statistical significance is described only when the recorded exact McNemar p-value is below 0.05.</p></section>
<section><h2>9. Error analysis</h2><div class="two"><div><h3>Rejected rewrites</h3>{html_table(rejected, [("pair_id","Pair"),("generation_status","Status"),("rejection_reason","Reason"),("text","Text")])}</div>
<div><h3>False negatives after rewriting</h3>{html_table(false_negatives[false_negatives.get("condition", pd.Series(index=false_negatives.index)).eq(REWRITE)] if not false_negatives.empty else false_negatives, [("model","Model"),("pair_id","Pair"),("text","Rewrite"),("phishing_probability","Probability")])}</div>
<div><h3>False positives on legitimate banking SMS</h3>{html_table(false_positives, [("model","Model"),("condition","Condition"),("pair_id","Pair"),("text","Text"),("phishing_probability","Probability")])}</div>
<div><h3>Prediction changes</h3>{html_table(changed, [("model","Model"),("pair_id","Pair"),("prediction_original","Original prediction"),("prediction_rewrite","Rewrite prediction"),("confidence_drop","Confidence drop")])}</div></div></section>
<section class="interpretation"><h2>10. Conservative interpretation</h2><ul>{statements}</ul><p class="meta">A null or small change is a valid experimental result. Confidence sensitivity is distinguished from classification failure.</p></section>
<footer>Generated from local experiment files. Source messages are HTML-escaped and any live URL schemes are defanged for display. The builder does not call an API, train a model, modify labels, or alter rewrite_pairs.csv.</footer>
</main></body></html>"""
    index = output_dir / "index.html"
    index.write_text(document, encoding="utf-8")
    if file_sha256(pairs_path) != source_hash:
        raise RuntimeError("Source rewrite_pairs.csv changed while building the dashboard")
    return index


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pairs", type=Path, default=DEFAULT_PAIRS)
    parser.add_argument("--results-dir", type=Path, default=DEFAULT_RESULTS)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    index = build_dashboard(args.pairs, args.results_dir, args.output_dir)
    print(f"Dashboard: {index}")
    print(f"Figures: {args.output_dir / 'figures'}")


if __name__ == "__main__":
    main()
