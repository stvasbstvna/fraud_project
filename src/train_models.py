"""Train the primary TF-IDF + Logistic Regression baseline."""

from __future__ import annotations

import argparse
from pathlib import Path

import joblib
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from sklearn.feature_extraction.text import TfidfVectorizer


def build_logistic_baseline(random_state: int = 42) -> Pipeline:
    return Pipeline([
        ("tfidf", TfidfVectorizer(ngram_range=(1, 2), min_df=2, max_df=0.98, sublinear_tf=True)),
        ("model", LogisticRegression(max_iter=2000, class_weight="balanced", random_state=random_state)),
    ])


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path)
    parser.add_argument("model_output", type=Path)
    parser.add_argument("--text-column", default="text")
    parser.add_argument("--label-column", default="class_label")
    parser.add_argument("--split-column", default="split")
    args = parser.parse_args()
    frame = pd.read_csv(args.input)
    train = frame[frame[args.split_column].eq("train")]
    if train.empty:
        raise ValueError("No rows with split=train")
    model = build_logistic_baseline()
    model.fit(train[args.text_column].fillna(""), train[args.label_column])
    args.model_output.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(model, args.model_output)


if __name__ == "__main__":
    main()
