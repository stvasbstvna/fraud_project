from pathlib import Path
import pandas as pd

INPUT_PATH = Path("data/pilot/confirmed_banking_pilot.csv")
OUTPUT_DIR = Path("data/generated")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

OUTPUT_PATH = OUTPUT_DIR / "ai_rewritten_pairs_template.csv"

df = pd.read_csv(INPUT_PATH)

# Keep phishing/smishing rows only for the rewrite experiment
df = df[df["label"].astype(str).str.lower().isin([
    "phishing", "smishing", "scam", "fraud", "malicious", "1"
])].copy()

# Split by model result
missed = df[df["predicted_label"].astype(str).str.lower() == "non_phishing"].copy()
detected = df[df["predicted_label"].astype(str).str.lower() == "phishing"].copy()

# Sample: include all missed if <= 10, then add detected examples
missed_sample = missed.sample(n=min(10, len(missed)), random_state=42)

# Try to balance human and AI-generated from detected examples
detected_human = detected[detected["is_human_written"].astype(str).str.upper() == "TRUE"]
detected_ai = detected[detected["is_ai_generated"].astype(str).str.upper() == "TRUE"]
detected_unknown = detected[
    (detected["is_human_written"].astype(str).str.lower() == "unknown") |
    (detected["is_ai_generated"].astype(str).str.lower() == "unknown")
]

parts = [missed_sample]

if len(detected_human) > 0:
    parts.append(detected_human.sample(n=min(8, len(detected_human)), random_state=42))

if len(detected_ai) > 0:
    parts.append(detected_ai.sample(n=min(8, len(detected_ai)), random_state=42))

if len(detected_unknown) > 0:
    parts.append(detected_unknown.sample(n=min(4, len(detected_unknown)), random_state=42))

sample = pd.concat(parts).drop_duplicates(subset=["id"]).reset_index(drop=True)

# If still fewer than 30, fill with more detected rows
if len(sample) < 30:
    remaining = detected[~detected["id"].isin(sample["id"])]
    extra = remaining.sample(n=min(30 - len(sample), len(remaining)), random_state=24)
    sample = pd.concat([sample, extra]).drop_duplicates(subset=["id"]).reset_index(drop=True)

# Limit to 30
sample = sample.head(30).copy()

out = pd.DataFrame()
out["pair_id"] = [f"pair_{i+1:03d}" for i in range(len(sample))]
out["original_id"] = sample["id"]
out["source_dataset"] = sample["source_dataset"]
out["is_human_written"] = sample["is_human_written"]
out["is_ai_generated"] = sample["is_ai_generated"]
out["is_ai_rewritten"] = "FALSE"
out["original_label"] = sample["label"]
out["original_text"] = sample["text"]
out["original_prediction"] = sample["predicted_label"]
out["original_phishing_probability"] = sample["phishing_probability"]
out["manual_requested_action"] = sample.get("manual_requested_action", "")
out["manual_intent_type"] = sample.get("manual_intent_type", "")
out["manual_brand_mentioned"] = sample.get("manual_brand_mentioned", "")
out["rewritten_text"] = ""
out["rewrite_style"] = "professional_less_suspicious"
out["same_intent_verified"] = ""
out["rewrite_notes"] = ""

out.to_csv(OUTPUT_PATH, index=False)

print(f"Saved rewrite template to: {OUTPUT_PATH}")
print("Rows:", len(out))
print("\nOriginal prediction distribution:")
print(out["original_prediction"].value_counts())
print("\nSource distribution:")
print(out["source_dataset"].value_counts())