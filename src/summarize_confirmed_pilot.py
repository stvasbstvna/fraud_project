from pathlib import Path
import pandas as pd

INPUT_PATH = Path("data/pilot/confirmed_banking_pilot.csv")
OUTPUT_DIR = Path("results")
OUTPUT_DIR.mkdir(exist_ok=True)

SUMMARY_PATH = OUTPUT_DIR / "confirmed_banking_pilot_summary.csv"

df = pd.read_csv(INPUT_PATH)

summary_rows = []

summary_rows.append({
    "metric": "total_confirmed_banking_rows",
    "value": len(df)
})

if "source_dataset" in df.columns:
    for source, count in df["source_dataset"].value_counts().items():
        summary_rows.append({
            "metric": f"rows_from_{source}",
            "value": count
        })

if "is_human_written" in df.columns:
    for value, count in df["is_human_written"].astype(str).value_counts().items():
        summary_rows.append({
            "metric": f"is_human_written_{value}",
            "value": count
        })

if "is_ai_generated" in df.columns:
    for value, count in df["is_ai_generated"].astype(str).value_counts().items():
        summary_rows.append({
            "metric": f"is_ai_generated_{value}",
            "value": count
        })

if "predicted_label" in df.columns:
    for value, count in df["predicted_label"].value_counts().items():
        summary_rows.append({
            "metric": f"baseline_predicted_{value}",
            "value": count
        })

if "phishing_probability" in df.columns:
    summary_rows.append({
        "metric": "average_phishing_probability",
        "value": round(df["phishing_probability"].mean(), 4)
    })

if "manual_requested_action" in df.columns:
    for value, count in df["manual_requested_action"].astype(str).value_counts().head(10).items():
        summary_rows.append({
            "metric": f"manual_requested_action_{value}",
            "value": count
        })

if "manual_intent_type" in df.columns:
    for value, count in df["manual_intent_type"].astype(str).value_counts().head(10).items():
        summary_rows.append({
            "metric": f"manual_intent_type_{value}",
            "value": count
        })

summary = pd.DataFrame(summary_rows)
summary.to_csv(SUMMARY_PATH, index=False)

print(summary.to_string(index=False))
print(f"\nSaved summary to: {SUMMARY_PATH}")