from pathlib import Path
import pandas as pd

INPUT_PATH = Path("data/pilot/confirmed_banking_pilot.csv")
OUTPUT_DIR = Path("results")
OUTPUT_DIR.mkdir(exist_ok=True)

OUTPUT_PATH = OUTPUT_DIR / "confirmed_banking_pilot_misses.csv"

df = pd.read_csv(INPUT_PATH)

misses = df[df["predicted_label"].astype(str).str.lower() == "non_phishing"].copy()

cols = [
    "id",
    "text",
    "label",
    "channel",
    "source_dataset",
    "is_human_written",
    "is_ai_generated",
    "phishing_probability",
    "manual_requested_action",
    "manual_intent_type",
    "manual_brand_mentioned",
    "manual_notes"
]

cols = [c for c in cols if c in misses.columns]
misses[cols].to_csv(OUTPUT_PATH, index=False)

print("Confirmed banking pilot misses:", len(misses))
print(misses[["id", "source_dataset", "channel", "phishing_probability"]].to_string(index=False))
print(f"\nSaved misses to: {OUTPUT_PATH}")