"""Train and evaluate the fixed Logistic Regression and Random Forest detectors.

Only rows with split=train are fitted.  The banking_test split is never used
for fitting or tuning.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import joblib
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    accuracy_score,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
)
from sklearn.pipeline import Pipeline


DEFAULT_INPUT = Path("data/final/sms_master_with_splits.csv")
DEFAULT_MODEL_DIR = Path("models/final")
DEFAULT_RESULT_DIR = Path("results/final_detectors")


def logistic_pipeline() -> Pipeline:
    return Pipeline(
        [
            (
                "tfidf",
                TfidfVectorizer(
                    lowercase=True,
                    stop_words="english",
                    ngram_range=(1, 2),
                    min_df=2,
                    max_df=0.95,
                    max_features=50_000,
                    sublinear_tf=True,
                ),
            ),
            (
                "classifier",
                LogisticRegression(
                    max_iter=2_000,
                    class_weight="balanced",
                    random_state=42,
                ),
            ),
        ]
    )


def random_forest_pipeline() -> Pipeline:
    return Pipeline(
        [
            (
                "tfidf",
                TfidfVectorizer(
                    lowercase=True,
                    stop_words="english",
                    ngram_range=(1, 2),
                    min_df=2,
                    max_df=0.95,
                    max_features=20_000,
                    sublinear_tf=True,
                ),
            ),
            (
                "classifier",
                RandomForestClassifier(
                    n_estimators=400,
                    min_samples_leaf=2,
                    max_features="sqrt",
                    class_weight="balanced_subsample",
                    random_state=42,
                    n_jobs=-1,
                ),
            ),
        ]
    )


def metric_row(model_name: str, split: str, y_true: pd.Series, y_pred, y_prob) -> dict[str, object]:
    tn, fp, fn, tp = confusion_matrix(y_true, y_pred, labels=[0, 1]).ravel()
    row: dict[str, object] = {
        "model": model_name,
        "split": split,
        "rows": int(len(y_true)),
        "accuracy": accuracy_score(y_true, y_pred),
        "precision": precision_score(y_true, y_pred, zero_division=0),
        "recall": recall_score(y_true, y_pred, zero_division=0),
        "f1": f1_score(y_true, y_pred, zero_division=0),
        "true_negatives": int(tn),
        "false_positives": int(fp),
        "false_negatives": int(fn),
        "true_positives": int(tp),
        "false_negative_rate": float(fn / (fn + tp)) if fn + tp else None,
    }
    row["roc_auc"] = (
        roc_auc_score(y_true, y_prob) if pd.Series(y_true).nunique() == 2 else None
    )
    return row


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT)
    parser.add_argument("--model-dir", type=Path, default=DEFAULT_MODEL_DIR)
    parser.add_argument("--result-dir", type=Path, default=DEFAULT_RESULT_DIR)
    args = parser.parse_args()

    frame = pd.read_csv(args.input)
    required = {"id", "text", "binary_label", "split", "source_dataset"}
    missing = sorted(required.difference(frame.columns))
    if missing:
        raise ValueError(f"Input dataset is missing columns: {missing}")

    train = frame[frame["split"].eq("train")].copy()
    if train.empty:
        raise ValueError("No rows with split=train")

    args.model_dir.mkdir(parents=True, exist_ok=True)
    args.result_dir.mkdir(parents=True, exist_ok=True)

    models = {
        "tfidf_logistic_regression": logistic_pipeline(),
        "tfidf_random_forest": random_forest_pipeline(),
    }
    metrics: list[dict[str, object]] = []
    predictions: list[pd.DataFrame] = []

    for model_name, model in models.items():
        model.fit(train["text"].fillna(""), train["binary_label"])
        joblib.dump(model, args.model_dir / f"{model_name}.joblib")

        for split in ("validation", "banking_test"):
            test = frame[frame["split"].eq(split)].copy()
            y_pred = model.predict(test["text"].fillna(""))
            y_prob = model.predict_proba(test["text"].fillna(""))[:, 1]
            metrics.append(metric_row(model_name, split, test["binary_label"], y_pred, y_prob))

            output = test[
                [
                    "id", "source_dataset", "text", "label", "binary_label",
                    "banking_decision", "split",
                ]
            ].copy()
            output.insert(0, "model", model_name)
            output["predicted_binary_label"] = y_pred
            output["phishing_probability"] = y_prob
            output["is_correct"] = output["binary_label"].eq(output["predicted_binary_label"])
            predictions.append(output)

    metrics_frame = pd.DataFrame(metrics)
    predictions_frame = pd.concat(predictions, ignore_index=True)
    metrics_frame.to_csv(args.result_dir / "metrics_by_model_and_split.csv", index=False, lineterminator="\n")
    predictions_frame.to_csv(args.result_dir / "predictions.csv", index=False, lineterminator="\n")
    predictions_frame[
        predictions_frame["binary_label"].eq(1)
        & predictions_frame["predicted_binary_label"].eq(0)
    ].to_csv(args.result_dir / "false_negatives.csv", index=False, lineterminator="\n")

    with open(args.result_dir / "run_metadata.json", "w", encoding="utf-8") as file:
        json.dump(
            {
                "input": args.input.as_posix(),
                "random_state": 42,
                "fit_split": "train",
                "evaluation_splits": ["validation", "banking_test"],
                "train_rows": int(len(train)),
                "models": list(models),
            },
            file,
            indent=2,
        )

    print(metrics_frame.to_string(index=False))
    print(f"\nSaved models to: {args.model_dir}")
    print(f"Saved results to: {args.result_dir}")


if __name__ == "__main__":
    main()
