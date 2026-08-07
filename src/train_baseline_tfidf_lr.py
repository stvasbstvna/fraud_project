import json
from pathlib import Path

import joblib
import pandas as pd
import matplotlib.pyplot as plt

from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    confusion_matrix,
    classification_report
)

DATA_PATH = Path("data/processed/unified_text_messages.csv")
MODEL_DIR = Path("models")
RESULTS_DIR = Path("results")

MODEL_DIR.mkdir(exist_ok=True)
RESULTS_DIR.mkdir(exist_ok=True)

MODEL_PATH = MODEL_DIR / "tfidf_logistic_regression.joblib"
PREDICTIONS_PATH = RESULTS_DIR / "baseline_tfidf_lr_predictions.csv"
METRICS_PATH = RESULTS_DIR / "baseline_tfidf_lr_metrics.json"
REPORT_PATH = RESULTS_DIR / "baseline_tfidf_lr_classification_report.txt"
CONFUSION_PATH = RESULTS_DIR / "baseline_tfidf_lr_confusion_matrix.png"


def normalize_label(value):
    if pd.isna(value):
        return None

    label = str(value).strip().lower()

    phishing_labels = {
        "1", "phishing", "smishing", "scam", "fraud", "malicious"
    }

    non_phishing_labels = {
        "0", "legitimate", "ham", "benign", "normal", "valid", "spam"
    }

    if label in phishing_labels:
        return 1

    if label in non_phishing_labels:
        return 0

    return None


def main():
    df = pd.read_csv(DATA_PATH)

    if "text" not in df.columns:
        raise ValueError("Expected a 'text' column in unified_text_messages.csv")

    if "label" not in df.columns:
        raise ValueError("Expected a 'label' column in unified_text_messages.csv")

    df["binary_label"] = df["label"].apply(normalize_label)

    df = df.dropna(subset=["text", "binary_label"]).copy()
    df["text"] = df["text"].astype(str)
    df["binary_label"] = df["binary_label"].astype(int)

    print("Usable rows:", len(df))
    print("Binary label distribution:")
    print(df["binary_label"].value_counts())

    X_train, X_test, y_train, y_test = train_test_split(
        df["text"],
        df["binary_label"],
        test_size=0.20,
        random_state=42,
        stratify=df["binary_label"]
    )

    model = Pipeline([
        ("tfidf", TfidfVectorizer(
            lowercase=True,
            stop_words="english",
            ngram_range=(1, 2),
            min_df=2,
            max_df=0.95,
            max_features=50000
        )),
        ("clf", LogisticRegression(
            max_iter=1000,
            class_weight="balanced",
            random_state=42
        ))
    ])

    model.fit(X_train, y_train)

    y_pred = model.predict(X_test)
    y_prob = model.predict_proba(X_test)[:, 1]

    cm = confusion_matrix(y_test, y_pred)
    tn, fp, fn, tp = cm.ravel()

    metrics = {
        "rows_used": int(len(df)),
        "train_rows": int(len(X_train)),
        "test_rows": int(len(X_test)),
        "accuracy": float(accuracy_score(y_test, y_pred)),
        "precision": float(precision_score(y_test, y_pred, zero_division=0)),
        "recall": float(recall_score(y_test, y_pred, zero_division=0)),
        "f1": float(f1_score(y_test, y_pred, zero_division=0)),
        "true_negatives": int(tn),
        "false_positives": int(fp),
        "false_negatives": int(fn),
        "true_positives": int(tp),
        "false_negative_rate": float(fn / (fn + tp)) if (fn + tp) > 0 else None,
    }

    print("\nMetrics:")
    print(json.dumps(metrics, indent=2))

    report = classification_report(
        y_test,
        y_pred,
        target_names=["non_phishing", "phishing"]
    )

    print("\nClassification report:")
    print(report)

    joblib.dump(model, MODEL_PATH)

    with open(METRICS_PATH, "w", encoding="utf-8") as f:
        json.dump(metrics, f, indent=2)

    with open(REPORT_PATH, "w", encoding="utf-8") as f:
        f.write(report)

    test_df = df.loc[X_test.index].copy()
    test_df["true_binary_label"] = y_test.values
    test_df["predicted_binary_label"] = y_pred
    test_df["phishing_probability"] = y_prob
    test_df.to_csv(PREDICTIONS_PATH, index=False)

    plt.figure(figsize=(5, 4))
    plt.imshow(cm)
    plt.title("TF-IDF + Logistic Regression Confusion Matrix")
    plt.xticks([0, 1], ["non_phishing", "phishing"], rotation=30)
    plt.yticks([0, 1], ["non_phishing", "phishing"])
    plt.xlabel("Predicted")
    plt.ylabel("True")

    for i in range(2):
        for j in range(2):
            plt.text(j, i, cm[i, j], ha="center", va="center")

    plt.tight_layout()
    plt.savefig(CONFUSION_PATH, dpi=200)

    print(f"\nSaved model to: {MODEL_PATH}")
    print(f"Saved predictions to: {PREDICTIONS_PATH}")
    print(f"Saved metrics to: {METRICS_PATH}")
    print(f"Saved report to: {REPORT_PATH}")
    print(f"Saved confusion matrix to: {CONFUSION_PATH}")


if __name__ == "__main__":
    main()