from pathlib import Path
import pandas as pd

INPUT_PATH = Path("data/pilot/confirmed_banking_pilot.csv")
OUTPUT_DIR = Path("results")
OUTPUT_DIR.mkdir(exist_ok=True)

OUTPUT_PATH = OUTPUT_DIR / "confirmed_human_vs_ai_comparison.csv"

df = pd.read_csv(INPUT_PATH)

groups = []

def summarize_group(group_name, group_df):
    total = len(group_df)

    predicted_phishing = int((group_df["predicted_label"].astype(str).str.lower() == "phishing").sum())
    predicted_non_phishing = int((group_df["predicted_label"].astype(str).str.lower() == "non_phishing").sum())

    avg_prob = group_df["phishing_probability"].mean() if total > 0 else 0
    fnr = predicted_non_phishing / total if total > 0 else 0

    return {
        "group": group_name,
        "rows": total,
        "predicted_phishing": predicted_phishing,
        "predicted_non_phishing_possible_false_negatives": predicted_non_phishing,
        "average_phishing_probability": round(avg_prob, 4),
        "possible_false_negative_rate": round(fnr, 4)
    }

human = df[df["is_human_written"].astype(str).str.upper() == "TRUE"]
ai = df[df["is_ai_generated"].astype(str).str.upper() == "TRUE"]
unknown = df[
    (df["is_human_written"].astype(str).str.lower() == "unknown") |
    (df["is_ai_generated"].astype(str).str.lower() == "unknown")
]

groups.append(summarize_group("human_written", human))
groups.append(summarize_group("llm_generated", ai))
groups.append(summarize_group("unknown_authorship_smishx", unknown))

summary = pd.DataFrame(groups)
summary.to_csv(OUTPUT_PATH, index=False)

print(summary.to_string(index=False))
print(f"\nSaved comparison to: {OUTPUT_PATH}")