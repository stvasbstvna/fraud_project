"""Evaluate overall and subgroup metrics, including rewrite detection gaps."""

from __future__ import annotations

import argparse
from pathlib import Path

import joblib
import pandas as pd
from sklearn.metrics import accuracy_score, precision_recall_fscore_support, confusion_matrix


def binary_metrics(y_true, y_pred, positive_label="phishing_scam") -> dict[str, float]:
    precision, recall, f1, _ = precision_recall_fscore_support(
        y_true, y_pred, labels=[positive_label], average=None, zero_division=0
    )
    labels = [positive_label, "legitimate"]
    cm = confusion_matrix(y_true, y_pred, labels=labels)
    false_negatives = cm[0, 1]
    positives = cm[0].sum()
    return {
        "accuracy": accuracy_score(y_true, y_pred),
        "precision": float(precision[0]),
        "recall": float(recall[0]),
        "f1": float(f1[0]),
        "false_negative_rate": float(false_negatives / positives) if positives else 0.0,
        "n": len(y_true),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path)
    parser.add_argument("model", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--text-column", default="text")
    parser.add_argument("--label-column", default="class_label")
    parser.add_argument("--split", default="test")
    args = parser.parse_args()
    frame = pd.read_csv(args.input)
    test = frame[frame["split"].eq(args.split)].copy()
    model = joblib.load(args.model)
    test["prediction"] = model.predict(test[args.text_column].fillna(""))
    rows = [{"group": "overall", **binary_metrics(test[args.label_column], test.prediction)}]
    for column in ["authorship", "channel"]:
        if column in test:
            for value, group in test.groupby(column, dropna=False):
                rows.append({"group": f"{column}={value}", **binary_metrics(group[args.label_column], group.prediction)})
    result = pd.DataFrame(rows)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    result.to_csv(args.output, index=False)


if __name__ == "__main__":
    main()
