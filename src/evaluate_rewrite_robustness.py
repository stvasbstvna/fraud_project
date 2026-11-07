"""Evaluate paired original/LLM rewrites with frozen detectors (never fit models)."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from scipy.stats import binomtest
from sklearn.metrics import accuracy_score, confusion_matrix, f1_score, precision_score, recall_score


DEFAULT_INPUT = Path("data/rewrite_experiment/rewrite_pairs.csv")
DEFAULT_MODEL_DIR = Path("models/final")
DEFAULT_HASHES = Path("results/rewrite_experiment/model_hashes.csv")
DEFAULT_OUT = Path("results/rewrite_experiment")


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def verify_hashes(path: Path) -> None:
    expected = pd.read_csv(path)
    for row in expected.itertuples(index=False):
        model_path = Path(row.model_file)
        observed = sha256(model_path)
        if observed != row.sha256:
            raise ValueError(f"Frozen model hash changed: {model_path}")


def condition_metrics(model: str, condition: str, data: pd.DataFrame) -> dict[str, object]:
    tn, fp, fn, tp = confusion_matrix(
        data["binary_label"], data["predicted_binary_label"], labels=[0, 1]
    ).ravel()
    specificity = tn / (tn + fp) if tn + fp else np.nan
    recall = recall_score(data["binary_label"], data["predicted_binary_label"], zero_division=0)
    return {
        "model": model,
        "condition": condition,
        "rows": len(data),
        "accuracy": accuracy_score(data["binary_label"], data["predicted_binary_label"]),
        "precision": precision_score(data["binary_label"], data["predicted_binary_label"], zero_division=0),
        "recall": recall,
        "f1": f1_score(data["binary_label"], data["predicted_binary_label"], zero_division=0),
        "specificity": specificity,
        "false_positive_rate": 1 - specificity if not np.isnan(specificity) else np.nan,
        "balanced_accuracy": (recall + specificity) / 2 if not np.isnan(specificity) else np.nan,
        "false_negative_rate": fn / (fn + tp) if fn + tp else np.nan,
        "true_negatives": int(tn), "false_positives": int(fp),
        "false_negatives": int(fn), "true_positives": int(tp),
        "mean_phishing_probability": data["phishing_probability"].mean(),
    }


def bootstrap_mean_ci(values: np.ndarray, seed: int = 42, draws: int = 10_000) -> tuple[float, float]:
    if len(values) == 0:
        return np.nan, np.nan
    rng = np.random.default_rng(seed)
    samples = rng.choice(values, size=(draws, len(values)), replace=True).mean(axis=1)
    return tuple(np.quantile(samples, [0.025, 0.975]))


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT)
    parser.add_argument("--model-dir", type=Path, default=DEFAULT_MODEL_DIR)
    parser.add_argument("--hashes", type=Path, default=DEFAULT_HASHES)
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    parser.add_argument(
        "--allow-pending-review", action="store_true",
        help="Exploratory pilot only; final analysis requires approved human review",
    )
    args = parser.parse_args()
    verify_hashes(args.hashes)
    frame = pd.read_csv(args.input, keep_default_na=False)

    originals = frame[frame["condition"].eq("T0_original")].copy()
    rewrites = frame[
        frame["condition"].eq("T1_llm_neutral_rewrite")
        & frame["generation_status"].eq("completed")
        & frame["safety_check_passed"].astype(str).str.lower().eq("true")
    ].copy()
    if not args.allow_pending_review:
        rewrites = rewrites[rewrites["human_review_status"].eq("approved")].copy()
    if rewrites.empty:
        raise ValueError("No eligible rewrites. Complete generation and human review first.")
    originals = originals[originals["pair_id"].isin(rewrites["pair_id"])].copy()
    if originals["pair_id"].duplicated().any() or rewrites["pair_id"].duplicated().any():
        raise ValueError("Expected exactly one original and one rewrite per pair_id")
    if set(originals["pair_id"]) != set(rewrites["pair_id"]):
        raise ValueError("Original/rewrite pair IDs do not match")

    args.out.mkdir(parents=True, exist_ok=True)
    model_paths = {
        "tfidf_logistic_regression": args.model_dir / "tfidf_logistic_regression.joblib",
        "tfidf_random_forest": args.model_dir / "tfidf_random_forest.joblib",
    }
    prediction_frames = []
    metric_rows = []
    transition_rows = []
    statistical_rows = []

    for model_name, model_path in model_paths.items():
        model = joblib.load(model_path)
        by_condition = []
        for condition, data in [("T0_original", originals), ("T1_llm_neutral_rewrite", rewrites)]:
            scored = data.copy()
            scored.insert(0, "model", model_name)
            scored["predicted_binary_label"] = model.predict(scored["text"])
            scored["phishing_probability"] = model.predict_proba(scored["text"])[:, 1]
            scored["is_correct"] = scored["binary_label"].eq(scored["predicted_binary_label"])
            prediction_frames.append(scored)
            by_condition.append(scored)
            metric_rows.append(condition_metrics(model_name, condition, scored))

        before = by_condition[0][
            ["pair_id", "binary_label", "predicted_binary_label", "phishing_probability"]
        ].rename(columns={
            "predicted_binary_label": "prediction_original",
            "phishing_probability": "probability_original",
        })
        after = by_condition[1][
            ["pair_id", "predicted_binary_label", "phishing_probability"]
        ].rename(columns={
            "predicted_binary_label": "prediction_rewrite",
            "phishing_probability": "probability_rewrite",
        })
        paired = before.merge(after, on="pair_id", validate="one_to_one")
        paired["confidence_drop"] = paired["probability_original"] - paired["probability_rewrite"]

        for label, label_name in [(1, "phishing"), (0, "non_phishing")]:
            subset = paired[paired["binary_label"].eq(label)]
            counts = subset.groupby(["prediction_original", "prediction_rewrite"]).size()
            for before_pred in (0, 1):
                for after_pred in (0, 1):
                    transition_rows.append({
                        "model": model_name, "true_label": label_name,
                        "prediction_original": before_pred,
                        "prediction_rewrite": after_pred,
                        "rows": int(counts.get((before_pred, after_pred), 0)),
                    })

        phish = paired[paired["binary_label"].eq(1)].copy()
        detected_original = phish["prediction_original"].eq(1)
        success = detected_original & phish["prediction_rewrite"].eq(0)
        recovered = phish["prediction_original"].eq(0) & phish["prediction_rewrite"].eq(1)
        b = int(success.sum())
        c = int(recovered.sum())
        p_value = float(binomtest(min(b, c), b + c, 0.5).pvalue) if b + c else 1.0
        ci_low, ci_high = bootstrap_mean_ci(phish["confidence_drop"].to_numpy())
        original_recall = float(phish["prediction_original"].mean())
        rewrite_recall = float(phish["prediction_rewrite"].mean())
        statistical_rows.append({
            "model": model_name,
            "phishing_pairs": len(phish),
            "original_recall": original_recall,
            "rewrite_recall": rewrite_recall,
            "recall_drop": original_recall - rewrite_recall,
            "original_fnr": 1 - original_recall,
            "rewrite_fnr": 1 - rewrite_recall,
            "fnr_increase": original_recall - rewrite_recall,
            "originally_detected": int(detected_original.sum()),
            "became_false_negative": b,
            "attack_success_rate": b / detected_original.sum() if detected_original.sum() else np.nan,
            "mean_confidence_drop": phish["confidence_drop"].mean(),
            "confidence_drop_ci95_low": ci_low,
            "confidence_drop_ci95_high": ci_high,
            "mcnemar_original_detected_rewrite_missed": b,
            "mcnemar_original_missed_rewrite_detected": c,
            "mcnemar_exact_p_value": p_value,
        })

    predictions = pd.concat(prediction_frames, ignore_index=True)
    metrics = pd.DataFrame(metric_rows)
    transitions = pd.DataFrame(transition_rows)
    statistics = pd.DataFrame(statistical_rows)
    predictions.to_csv(args.out / "paired_predictions.csv", index=False, lineterminator="\n")
    metrics.to_csv(args.out / "metrics_by_model_and_condition.csv", index=False, lineterminator="\n")
    transitions.to_csv(args.out / "paired_transition_table.csv", index=False, lineterminator="\n")
    statistics.to_csv(args.out / "statistical_tests.csv", index=False, lineterminator="\n")
    predictions[
        predictions["binary_label"].eq(1)
        & predictions["predicted_binary_label"].eq(0)
    ].to_csv(args.out / "false_negatives_after_rewrite.csv", index=False, lineterminator="\n")
    summary = {
        "models": list(model_paths),
        "eligible_pairs": int(len(rewrites)),
        "human_review_required": not args.allow_pending_review,
        "detectors_retrained": False,
        "detector_feedback_used_for_generation": False,
    }
    (args.out / "rewrite_experiment_summary.json").write_text(
        json.dumps(summary, indent=2), encoding="utf-8"
    )
    print(metrics.to_string(index=False))
    print("\nPaired robustness statistics:")
    print(statistics.to_string(index=False))


if __name__ == "__main__":
    main()
