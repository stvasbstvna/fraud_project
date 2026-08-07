import pandas as pd
from pathlib import Path

PREDICTIONS_PATH = Path("results/baseline_tfidf_lr_predictions.csv")
OUTPUT_PATH = Path("results/baseline_false_negatives.csv")

df = pd.read_csv(PREDICTIONS_PATH)

false_negatives = df[
    (df["true_binary_label"] == 1) &
    (df["predicted_binary_label"] == 0)
].copy()

false_negatives = false_negatives.sort_values(
    by="phishing_probability",
    ascending=True
)

columns_to_keep = [
    "id",
    "text",
    "label",
    "source_dataset",
    "channel",
    "is_human_written",
    "is_ai_generated",
    "is_ai_rewritten",
    "phishing_probability",
    "notes"
]

existing_columns = [col for col in columns_to_keep if col in false_negatives.columns]

false_negatives[existing_columns].to_csv(OUTPUT_PATH, index=False)

print("False negatives:", len(false_negatives))
print(f"Saved to {OUTPUT_PATH}")

print("\nTop 10 strongest false negatives:")
for idx, row in false_negatives.head(10).iterrows():
    print("\n" + "-" * 80)
    print("ID:", row.get("id", ""))
    print("Source:", row.get("source_dataset", ""))
    print("Channel:", row.get("channel", ""))
    print("AI-generated:", row.get("is_ai_generated", ""))
    print("Human-written:", row.get("is_human_written", ""))
    print("Probability:", row.get("phishing_probability", ""))
    print("Text:", str(row.get("text", ""))[:700])