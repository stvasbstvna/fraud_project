from pathlib import Path
import pandas as pd

INPUT_PATH = Path("data/pilot/confirmed_banking_phishing_only.csv")
OUTPUT_DIR = Path("results")
OUTPUT_DIR.mkdir(exist_ok=True)

OUTPUT_PATH = OUTPUT_DIR / "phishing_only_human_vs_ai_comparison.csv"

df = pd.read_csv(INPUT_PATH)

def summarize_group(group_name, group_df):
    total = len(group_df)

    if total == 0:
        return {
            "group": group_name,
            "rows": 0,
            "predicted_phishing": 0,
            "false_negatives": 0,
            "average_phishing_probability": 0,
            "false_negative_rate": 0
        }

    pred = group_df["predicted_label"].astype(str).str.lower()
    predicted_phishing = int((pred == "phishing").sum())
    false_negatives = int((pred != "phishing").sum())
    avg_prob = round(group_df["phishing_probability"].mean(), 4)
    fnr = round(false_negatives / total, 4)

    return {
        "group": group_name,
        "rows": total,
        "predicted_phishing": predicted_phishing,
        "false_negatives": false_negatives,
        "average_phishing_probability": avg_prob,
        "false_negative_rate": fnr
    }

human = df[df["is_human_written"].astype(str).str.upper() == "TRUE"]
ai = df[df["is_ai_generated"].astype(str).str.upper() == "TRUE"]
unknown = df[
    (df["is_human_written"].astype(str).str.lower() == "unknown") |
    (df["is_ai_generated"].astype(str).str.lower() == "unknown")
]

summary = pd.DataFrame([
    summarize_group("human_written_phishing", human),
    summarize_group("llm_generated_phishing", ai),
    summarize_group("unknown_authorship_smishx_phishing", unknown),
])

summary.to_csv(OUTPUT_PATH, index=False)

print(summary.to_string(index=False))
print(f"\nSaved comparison to: {OUTPUT_PATH}")