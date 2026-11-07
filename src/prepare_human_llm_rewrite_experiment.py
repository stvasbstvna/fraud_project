"""Prepare separate human, existing-LLM, and human-to-LLM rewrite datasets."""

from pathlib import Path
import re
import pandas as pd

PILOT = Path("data/pilot/confirmed_banking_phishing_only.csv")
CONFIRMED = Path("data/pilot/confirmed_banking_pilot.csv")
OUT = Path("data/human_llm_rewrite_experiment")

URL_RE = re.compile(r"(?i)\b(?:https?://|hxxps?://|www\.)\S+")
PHONE_RE = re.compile(r"(?<!\w)(?:\+?\d[\d\s().-]{6,}\d)(?!\w)")
EMAIL_RE = re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b")

def val(row, manual, automatic, fallback):
    for col in (manual, automatic):
        x = row.get(col)
        if pd.notna(x) and str(x).strip().lower() not in {"", "nan", "unknown", "none"}:
            return str(x).strip()
    return fallback

def defang(row):
    text = str(row["text"])
    text = URL_RE.sub("[DEFANGED_LINK]", text)
    text = EMAIL_RE.sub("[EMAIL]", text)
    text = PHONE_RE.sub("[PHONE]", text)
    brand = val(row, "manual_brand_mentioned", "brand_mentioned", "")
    if brand and len(brand) > 2:
        text = re.sub(re.escape(brand), "[BANK_OR_SERVICE]", text, flags=re.I)
    return text

def common(row, sample_id):
    return {
        "sample_id": sample_id,
        "source_id": row["id"],
        "source_dataset": row["source_dataset"],
        "channel": row["channel"],
        "true_label": "phishing",
        "intent_type": val(row, "manual_intent_type", "intent_type", "banking account security"),
        "requested_action": val(row, "manual_requested_action", "requested_action", "review account notice"),
        "original_text": row["text"],
        "defanged_source_text": defang(row),
        "baseline_prediction": row["predicted_label"],
        "baseline_phishing_probability": row["phishing_probability"],
    }

def main():
    OUT.mkdir(parents=True, exist_ok=True)
    df = pd.read_csv(PILOT)
    human = df[df["is_human_written"].astype(str).str.lower().eq("true")].copy()
    llm = df[df["is_ai_generated"].astype(str).str.lower().eq("true")].copy()
    human = human.sort_values("id").reset_index(drop=True)
    llm = llm.sort_values("id").reset_index(drop=True)

    human_rows = [common(r, f"H{i:03d}") for i, (_, r) in enumerate(human.iterrows(), 1)]
    llm_rows = [common(r, f"L{i:03d}") for i, (_, r) in enumerate(llm.iterrows(), 1)]
    human_df, llm_df = pd.DataFrame(human_rows), pd.DataFrame(llm_rows)
    human_df.to_csv(OUT / "01_human_written_originals.csv", index=False)
    llm_df.to_csv(OUT / "02_existing_llm_generated.csv", index=False)

    rewrite = human_df.copy()
    rewrite.insert(7, "rewrite_prompt_id", "HR_P1")
    rewrite.insert(8, "rewrite_text", "")
    rewrite.insert(9, "generator_model", "")
    rewrite.insert(10, "generation_status", "pending")
    rewrite.insert(11, "same_intent_verified", "pending_manual_review")
    rewrite.insert(12, "no_new_operational_detail", "pending_manual_review")
    rewrite.to_csv(OUT / "03_human_to_llm_rewrite_input.csv", index=False)

    confirmed = pd.read_csv(CONFIRMED)
    legitimate = confirmed[confirmed["label"].astype(str).str.lower().isin(["legitimate", "ham", "benign", "normal", "valid", "0"])].copy()
    legitimate = legitimate.sort_values("id").reset_index(drop=True)
    legitimate[["id", "text", "channel", "source_dataset", "label", "predicted_label", "phishing_probability"]].rename(
        columns={"id":"sample_id", "label":"true_label", "predicted_label":"baseline_prediction", "phishing_probability":"baseline_phishing_probability"}
    ).to_csv(OUT / "04_fixed_legitimate_banking_controls.csv", index=False)

    human_df.head(33).to_csv(OUT / "05_matched_human_33.csv", index=False)
    llm_df.head(33).to_csv(OUT / "06_matched_llm_33.csv", index=False)
    print(f"human={len(human_df)}, llm={len(llm_df)}, legitimate_controls={len(legitimate)}")

if __name__ == "__main__":
    main()
