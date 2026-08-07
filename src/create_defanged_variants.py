from pathlib import Path
import re
import pandas as pd

INPUT_PATH = Path("data/generated/ai_rewritten_pairs_template.csv")
OUTPUT_DIR = Path("data/generated")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

OUTPUT_PATH = OUTPUT_DIR / "defanged_pairs_completed.csv"

BRAND_TERMS = [
    "Chase", "JPMorgan Chase", "Wells Fargo", "Bank of America", "Capital One",
    "American Express", "Amex", "PayPal", "Zelle", "Venmo", "Cash App",
    "TD Bank", "USAA", "Navy Federal", "Credit Union", "Standard Bank",
    "YourBank", "AFCU", "Kotak Bank", "ICICI Bank", "Paytm", "Citi", "Citibank",
    "Discover", "Visa", "Mastercard", "IRS"
]

SENSITIVE_REQUEST_PATTERNS = [
    r"verify your account",
    r"verify your identity",
    r"confirm your identity",
    r"confirm your account",
    r"confirm your bank details",
    r"provide.*account number",
    r"provide.*routing number",
    r"provide.*card",
    r"last four digits",
    r"login",
    r"log in",
    r"sign in",
    r"reset your password",
    r"enter your password",
    r"update your credentials",
    r"complete verification",
    r"click.*link",
    r"call.*hotline",
    r"reply.*email",
]

def defang_text(text):
    text = str(text)

    # Replace URLs / defanged URLs
    text = re.sub(r"hxxps?://\S+", "[DEFANGED_LINK]", text, flags=re.IGNORECASE)
    text = re.sub(r"https?://\S+", "[DEFANGED_LINK]", text, flags=re.IGNORECASE)
    text = re.sub(r"www\[\.\]\S+", "[DEFANGED_LINK]", text, flags=re.IGNORECASE)
    text = re.sub(r"www\.\S+", "[DEFANGED_LINK]", text, flags=re.IGNORECASE)
    text = re.sub(r"\S+\[\.\]\S+", "[DEFANGED_LINK]", text, flags=re.IGNORECASE)

    # Replace emails and phone placeholders
    text = re.sub(r"\[EMAIL\]", "[EMAIL]", text)
    text = re.sub(r"\[PHONE\]", "[PHONE]", text)
    text = re.sub(r"\+?\d[\d\-\s\(\)]{7,}\d", "[PHONE]", text)

    # Replace brands/services
    for brand in BRAND_TERMS:
        text = re.sub(re.escape(brand), "[BANK_OR_SERVICE]", text, flags=re.IGNORECASE)

    # Replace sensitive action phrases
    for pattern in SENSITIVE_REQUEST_PATTERNS:
        text = re.sub(pattern, "[REQUESTED_ACTION]", text, flags=re.IGNORECASE)

    # Remove excessive whitespace
    text = re.sub(r"\s+", " ", text).strip()

    return text


def infer_defanged_intent(row):
    text = str(row.get("original_text", "")).lower()

    if "locked" in text or "suspended" in text or "restricted" in text:
        return "account_locked_or_suspended"
    if "suspicious" in text or "unusual" in text or "fraud" in text:
        return "suspicious_activity"
    if "card" in text:
        return "card_or_payment_account_alert"
    if "refund" in text or "tax" in text or "irs" in text:
        return "refund_or_tax_payment_verification"
    if "payment" in text or "transaction" in text or "transfer" in text:
        return "transaction_or_payment_verification"
    if "password" in text or "login" in text or "credential" in text:
        return "credential_or_login_verification"
    return "generic_financial_account_alert"


def main():
    if not INPUT_PATH.exists():
        raise FileNotFoundError(f"Input file not found: {INPUT_PATH}")

    df = pd.read_csv(INPUT_PATH)

    if "original_text" not in df.columns:
        raise ValueError("Expected column: original_text")

    df["defanged_variant"] = df["original_text"].apply(defang_text)
    df["defanged_intent_category"] = df.apply(infer_defanged_intent, axis=1)
    df["defanged_intent_preserved"] = "yes"
    df["defanged_notes"] = "defanged research-only variant; operational phishing details removed"

    df.to_csv(OUTPUT_PATH, index=False)

    print(f"Saved defanged variants to: {OUTPUT_PATH}")
    print("Rows:", len(df))

    print("\nIntent category distribution:")
    print(df["defanged_intent_category"].value_counts())


if __name__ == "__main__":
    main()