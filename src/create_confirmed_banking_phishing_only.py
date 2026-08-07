from pathlib import Path
import pandas as pd

INPUT_PATH = Path("data/pilot/confirmed_banking_pilot.csv")
OUTPUT_DIR = Path("data/pilot")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

OUTPUT_PATH = OUTPUT_DIR / "confirmed_banking_phishing_only.csv"
SUMMARY_PATH = Path("results") / "confirmed_banking_phishing_only_summary.csv"
SUMMARY_PATH.parent.mkdir(exist_ok=True)

df = pd.read_csv(INPUT_PATH)

df["label_norm"] = df["label"].astype(str).str.lower().str.strip()
phishing = df[df["label_norm"].isin(["phishing", "smishing", "scam", "fraud", "malicious", "1"])].copy()

phishing.to_csv(OUTPUT_PATH, index=False)

summary_rows = [
    {"metric": "confirmed_banking_total_rows", "value": len(df)},
    {"metric": "confirmed_banking_phishing_only_rows", "value": len(phishing)},
]

if "source_dataset" in phishing.columns:
    for source, count in phishing["source_dataset"].value_counts().items():
        summary_rows.append({"metric": f"phishing_rows_from_{source}", "value": count})

if "is_human_written" in phishing.columns:
    for value, count in phishing["is_human_written"].astype(str).value_counts().items():
        summary_rows.append({"metric": f"is_human_written_{value}", "value": count})

if "is_ai_generated" in phishing.columns:
    for value, count in phishing["is_ai_generated"].astype(str).value_counts().items():
        summary_rows.append({"metric": f"is_ai_generated_{value}", "value": count})

summary = pd.DataFrame(summary_rows)
summary.to_csv(SUMMARY_PATH, index=False)

print(summary.to_string(index=False))
print(f"\nSaved phishing-only pilot to: {OUTPUT_PATH}")
print(f"Saved summary to: {SUMMARY_PATH}")