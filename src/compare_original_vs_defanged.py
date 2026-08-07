from pathlib import Path
import pandas as pd
import joblib

INPUT_PATH = Path("data/generated/defanged_pairs_completed.csv")
MODEL_PATH = Path("models/tfidf_logistic_regression.joblib")
OUTPUT_DIR = Path("results")
OUTPUT_DIR.mkdir(exist_ok=True)

OUTPUT_PATH = OUTPUT_DIR / "original_vs_defanged_comparison.csv"
SUMMARY_PATH = OUTPUT_DIR / "original_vs_defanged_summary.csv"

df = pd.read_csv(INPUT_PATH)
model = joblib.load(MODEL_PATH)

required_cols = ["pair_id", "original_text", "defanged_variant"]
for col in required_cols:
    if col not in df.columns:
        raise ValueError(f"Missing required column: {col}")

# Score original texts
original_probs = model.predict_proba(df["original_text"].astype(str))[:, 1]
original_preds = model.predict(df["original_text"].astype(str))

# Score defanged variants
defanged_probs = model.predict_proba(df["defanged_variant"].astype(str))[:, 1]
defanged_preds = model.predict(df["defanged_variant"].astype(str))

df["rescored_original_probability"] = original_probs
df["rescored_original_prediction"] = [
    "phishing" if x == 1 else "non_phishing" for x in original_preds
]

df["defanged_probability"] = defanged_probs
df["defanged_prediction"] = [
    "phishing" if x == 1 else "non_phishing" for x in defanged_preds
]

df["probability_change"] = df["defanged_probability"] - df["rescored_original_probability"]

df["original_missed"] = df["rescored_original_prediction"] == "non_phishing"
df["defanged_missed"] = df["defanged_prediction"] == "non_phishing"

df["became_missed_after_defanging"] = (
    (df["rescored_original_prediction"] == "phishing") &
    (df["defanged_prediction"] == "non_phishing")
)

summary = pd.DataFrame([
    {
        "set": "original",
        "rows": len(df),
        "avg_phishing_probability": round(df["rescored_original_probability"].mean(), 4),
        "predicted_phishing": int((df["rescored_original_prediction"] == "phishing").sum()),
        "predicted_non_phishing": int((df["rescored_original_prediction"] == "non_phishing").sum()),
        "possible_false_negative_rate": round((df["rescored_original_prediction"] == "non_phishing").mean(), 4),
    },
    {
        "set": "defanged",
        "rows": len(df),
        "avg_phishing_probability": round(df["defanged_probability"].mean(), 4),
        "predicted_phishing": int((df["defanged_prediction"] == "phishing").sum()),
        "predicted_non_phishing": int((df["defanged_prediction"] == "non_phishing").sum()),
        "possible_false_negative_rate": round((df["defanged_prediction"] == "non_phishing").mean(), 4),
    }
])

df.to_csv(OUTPUT_PATH, index=False)
summary.to_csv(SUMMARY_PATH, index=False)

print("Original vs defanged summary:")
print(summary.to_string(index=False))

print("\nBecame missed after defanging:")
print(int(df["became_missed_after_defanging"].sum()))

print(f"\nSaved detailed comparison to: {OUTPUT_PATH}")
print(f"Saved summary to: {SUMMARY_PATH}")