from pathlib import Path
import pandas as pd

INPUT_PATH = Path("data/pilot/confirmed_banking_pilot.csv")
OUTPUT_DIR = Path("results")
OUTPUT_DIR.mkdir(exist_ok=True)

SUMMARY_PATH = OUTPUT_DIR / "confirmed_banking_correct_evaluation_summary.csv"
MISSES_PATH = OUTPUT_DIR / "confirmed_banking_true_false_negatives.csv"
ALL_NON_PHISHING_PRED_PATH = OUTPUT_DIR / "confirmed_banking_predicted_non_phishing_review.csv"

df = pd.read_csv(INPUT_PATH)

# Normalize labels
df["label_norm"] = df["label"].astype(str).str.lower().str.strip()
df["pred_norm"] = df["predicted_label"].astype(str).str.lower().str.strip()

# Binary truth
df["true_is_phishing"] = df["label_norm"].isin(["phishing", "smishing", "scam", "fraud", "malicious", "1"])
df["pred_is_phishing"] = df["pred_norm"].eq("phishing")

# Confusion matrix components
tp = int(((df["true_is_phishing"] == True) & (df["pred_is_phishing"] == True)).sum())
fn = int(((df["true_is_phishing"] == True) & (df["pred_is_phishing"] == False)).sum())
tn = int(((df["true_is_phishing"] == False) & (df["pred_is_phishing"] == False)).sum())
fp = int(((df["true_is_phishing"] == False) & (df["pred_is_phishing"] == True)).sum())

total = len(df)
true_phishing = int(df["true_is_phishing"].sum())
true_non_phishing = total - true_phishing

accuracy = (tp + tn) / total if total else 0
precision = tp / (tp + fp) if (tp + fp) else 0
recall = tp / (tp + fn) if (tp + fn) else 0
f1 = 2 * precision * recall / (precision + recall) if (precision + recall) else 0
fnr = fn / (tp + fn) if (tp + fn) else 0
fpr = fp / (fp + tn) if (fp + tn) else 0

summary = pd.DataFrame([
    {"metric": "total_confirmed_banking_rows", "value": total},
    {"metric": "true_phishing_rows", "value": true_phishing},
    {"metric": "true_non_phishing_rows", "value": true_non_phishing},
    {"metric": "true_positives", "value": tp},
    {"metric": "false_negatives", "value": fn},
    {"metric": "true_negatives", "value": tn},
    {"metric": "false_positives", "value": fp},
    {"metric": "accuracy", "value": round(accuracy, 4)},
    {"metric": "precision", "value": round(precision, 4)},
    {"metric": "recall", "value": round(recall, 4)},
    {"metric": "f1", "value": round(f1, 4)},
    {"metric": "false_negative_rate", "value": round(fnr, 4)},
    {"metric": "false_positive_rate", "value": round(fpr, 4)},
    {"metric": "average_phishing_probability", "value": round(df["phishing_probability"].mean(), 4)},
])

# Save true false negatives only
true_fns = df[(df["true_is_phishing"] == True) & (df["pred_is_phishing"] == False)].copy()

cols = [
    "id", "text", "label", "channel", "source_dataset",
    "is_human_written", "is_ai_generated",
    "phishing_probability", "predicted_label",
    "manual_requested_action", "manual_intent_type",
    "manual_brand_mentioned", "manual_notes"
]
cols = [c for c in cols if c in df.columns]

true_fns[cols].to_csv(MISSES_PATH, index=False)

# Save all predicted non-phishing rows for review
pred_non_phishing = df[df["pred_is_phishing"] == False].copy()
pred_non_phishing[cols].to_csv(ALL_NON_PHISHING_PRED_PATH, index=False)

summary.to_csv(SUMMARY_PATH, index=False)

print("Correct evaluation summary:")
print(summary.to_string(index=False))

print("\nPredicted non-phishing rows:", len(pred_non_phishing))
print("True false negatives:", len(true_fns))

print(f"\nSaved summary to: {SUMMARY_PATH}")
print(f"Saved true false negatives to: {MISSES_PATH}")
print(f"Saved all predicted non-phishing review rows to: {ALL_NON_PHISHING_PRED_PATH}")