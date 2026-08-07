from pathlib import Path
import re

import joblib
import pandas as pd

MODEL_PATH = Path("models/tfidf_logistic_regression.joblib")
INPUT_PATH = Path("data/processed/banking_candidates.csv")

OUTPUT_DIR = Path("outputs")
OUTPUT_DIR.mkdir(exist_ok=True)

FULL_OUTPUT_PATH = OUTPUT_DIR / "banking_candidates_scored_and_filtered.csv"
PRIORITY_OUTPUT_PATH = OUTPUT_DIR / "banking_priority_review_sample.csv"


def contains_any(text, keywords):
    text = str(text).lower()
    return any(keyword in text for keyword in keywords)


def detect_requested_action(text):
    text = str(text).lower()

    if contains_any(text, ["click", "tap", "visit", "go to", "open link", "follow the link"]):
        return "click_link"

    if contains_any(text, ["verify", "verification", "confirm your account", "validate"]):
        return "verify_account"

    if contains_any(text, ["password", "login", "log in", "sign in", "credentials"]):
        return "enter_credentials"

    if contains_any(text, ["call", "phone", "dial"]):
        return "call_number"

    if contains_any(text, ["reply", "text back", "send code", "otp", "one-time code"]):
        return "reply_with_code"

    if contains_any(text, ["payment", "pay", "invoice", "fee", "charge", "unpaid"]):
        return "make_payment"

    if contains_any(text, ["attachment", "attached file", "download"]):
        return "open_attachment"

    return "unknown"


def detect_intent_type(text):
    text = str(text).lower()

    if contains_any(text, ["locked", "blocked", "restricted", "frozen"]):
        return "account_locked"

    if contains_any(text, ["suspicious", "fraud", "unauthorized", "unusual activity"]):
        return "suspicious_activity"

    if contains_any(text, ["payment failed", "declined", "unpaid", "fee"]):
        return "payment_failed"

    if contains_any(text, ["card suspended", "card blocked", "debit card", "credit card"]):
        return "card_suspended"

    if contains_any(text, ["refund", "reimbursement", "claim your refund"]):
        return "refund_claim"

    if contains_any(text, ["security", "secure", "protection", "alert"]):
        return "security_update"

    if contains_any(text, ["password reset", "reset your password"]):
        return "password_reset"

    if contains_any(text, ["invoice", "bill", "transaction", "transfer"]):
        return "invoice_or_payment"

    if contains_any(text, ["support", "help desk", "customer service"]):
        return "fake_support"

    if contains_any(text, ["bank", "account", "payment", "card"]):
        return "generic_bank_alert"

    return "unknown"


def detect_possible_bank_or_payment_brand(text):
    text = str(text).lower()

    brands = [
        "chase", "wells fargo", "bank of america", "capital one", "citi",
        "citibank", "discover", "american express", "amex", "paypal",
        "zelle", "venmo", "cash app", "stripe", "boa", "us bank",
        "bank", "credit union"
    ]

    matched = [brand for brand in brands if brand in text]
    return ", ".join(matched)


def has_url_like_pattern(text):
    text = str(text).lower()
    pattern = r"(http|hxxp|www\.|\[.\]|\.com|\.net|\.org|\.info|\.bank|\.io|\.lol)"
    return "yes" if re.search(pattern, text) else "no"


def main():
    if not MODEL_PATH.exists():
        raise FileNotFoundError("Model not found. Run train_baseline_tfidf_lr.py first.")

    if not INPUT_PATH.exists():
        raise FileNotFoundError("banking_candidates.csv not found.")

    model = joblib.load(MODEL_PATH)
    df = pd.read_csv(INPUT_PATH)

    df["text"] = df["text"].astype(str)

    df["predicted_binary_label"] = model.predict(df["text"])
    df["phishing_probability"] = model.predict_proba(df["text"])[:, 1]
    df["predicted_label"] = df["predicted_binary_label"].map({
        1: "phishing",
        0: "non_phishing"
    })

    df["auto_requested_action"] = df["text"].apply(detect_requested_action)
    df["auto_intent_type"] = df["text"].apply(detect_intent_type)
    df["auto_brand_mentioned"] = df["text"].apply(detect_possible_bank_or_payment_brand)
    df["auto_has_url_like_pattern"] = df["text"].apply(has_url_like_pattern)

    # Important rows for review:
    # 1. predicted non_phishing but original label says phishing
    # 2. low phishing probability but banking keyword exists
    # 3. possible banking/payment brand exists
    # 4. contains URL-like pattern
    df["priority_reason"] = ""

    df.loc[
        (df["label"].astype(str).str.lower() == "phishing") &
        (df["predicted_label"] == "non_phishing"),
        "priority_reason"
    ] += "possible_false_negative;"

    df.loc[
        df["phishing_probability"] < 0.50,
        "priority_reason"
    ] += "low_model_confidence_for_phishing;"

    df.loc[
        df["auto_brand_mentioned"].astype(str).str.len() > 0,
        "priority_reason"
    ] += "brand_or_payment_mention;"

    df.loc[
        df["auto_has_url_like_pattern"] == "yes",
        "priority_reason"
    ] += "url_like_pattern;"

    df.to_csv(FULL_OUTPUT_PATH, index=False)

    # Priority sample for manual review
    priority = df[df["priority_reason"].astype(str).str.len() > 0].copy()

    # balance sample: some from human, some from AI, some from SmishX
    sample_parts = []

    if "source_dataset" in priority.columns:
        for source in ["cross_model_human", "cross_model_llm", "SmishX"]:
            part = priority[priority["source_dataset"] == source]
            if len(part) > 0:
                sample_parts.append(part.sample(n=min(75, len(part)), random_state=42))

    if sample_parts:
        sample = pd.concat(sample_parts).drop_duplicates(subset=["id"]).reset_index(drop=True)
    else:
        sample = priority.sample(n=min(200, len(priority)), random_state=42)

    manual_cols = [
        "manual_banking_related",
        "manual_requested_action",
        "manual_intent_type",
        "manual_brand_mentioned",
        "manual_notes"
    ]

    for col in manual_cols:
        if col not in sample.columns:
            sample[col] = ""

    sample.to_csv(PRIORITY_OUTPUT_PATH, index=False)

    print(f"Saved full scored file to: {FULL_OUTPUT_PATH}")
    print(f"Saved priority manual review sample to: {PRIORITY_OUTPUT_PATH}")
    print("\nRows in full banking candidates:", len(df))
    print("Rows in priority sample:", len(sample))

    print("\nPrediction distribution:")
    print(df["predicted_label"].value_counts())

    print("\nTop priority reasons:")
    print(df["priority_reason"].value_counts().head(20))


if __name__ == "__main__":
    main()