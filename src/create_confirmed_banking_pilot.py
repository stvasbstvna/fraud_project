from pathlib import Path
import pandas as pd

INPUT_PATH = Path("outputs/banking_priority_review_sample.csv")
# if your reviewed file is somewhere else, change this line:
# INPUT_PATH = Path("outputs/banking_priority_review_sample_reviewed.csv")

OUTPUT_DIR = Path("data/pilot")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

CONFIRMED_OUTPUT = OUTPUT_DIR / "confirmed_banking_pilot.csv"
RECHECK_OUTPUT = OUTPUT_DIR / "needs_recheck_pilot.csv"
SUMMARY_OUTPUT = OUTPUT_DIR / "manual_review_summary.csv"


BANKING_STRONG_TERMS = [
    "bank", "banking", "credit card", "debit card", "card services",
    "paypal", "zelle", "venmo", "cash app", "paytm", "kotak",
    "chase", "wells fargo", "bank of america", "capital one",
    "american express", "amex", "citi", "citibank", "td bank",
    "navy federal", "credit union", "usaa", "standard bank",
    "icici", "afcu", "yourbank", "account number", "routing number",
    "online banking", "fraud prevention", "suspicious transaction",
    "account suspended", "account locked", "verify your account",
    "bank account", "bank details", "direct deposit", "wire transfer"
]

NON_BANKING_STRONG_TERMS = [
    "ups", "fedex", "usps", "parcel", "package", "delivery", "shipment",
    "casino", "bonus", "free spins", "play responsibly", "coupon",
    "mint mobile", "jio", "mcdelivery", "lybrate", "instagram",
    "microsoft 365", "mailbox", "cloud", "employee handbook",
    "benefits enrollment", "hr portal", "health", "medicine",
    "subscription", "newsletter", "survey", "property methods",
    "real estate course", "casino planet"
]


def contains_any(text, terms):
    text = str(text).lower()
    return any(term in text for term in terms)


def strict_banking_decision(row):
    text = str(row.get("text", "")).lower()
    source = str(row.get("source_dataset", ""))
    current_manual = str(row.get("manual_banking_related", "")).lower().strip()
    original_label = str(row.get("label", "")).lower().strip()

    strong_bank = contains_any(text, BANKING_STRONG_TERMS)
    strong_nonbank = contains_any(text, NON_BANKING_STRONG_TERMS)

    # Strong bank impersonation / finance-account logic
    if strong_bank and not strong_nonbank:
        return "yes", "strong banking/payment-account indicators"

    # Some tax/refund/payroll cases are financial but not bank impersonation
    if ("tax refund" in text or "refund" in text or "irs" in text) and (
        "bank account" in text or "banking details" in text or "direct deposit" in text or "routing number" in text
    ):
        return "yes", "financial credential/payment details requested"

    # Payment app / crypto / wallet can count as financial
    if any(term in text for term in ["paypal", "zelle", "paytm", "metamask", "wallet", "kucoin"]):
        return "yes", "payment app / financial platform"

    # Obvious non-bank categories
    if strong_nonbank and not strong_bank:
        return "no", "strong non-banking category"

    # If it only has weak generic words, do not count as confirmed banking
    weak_only = any(term in text for term in ["account", "payment", "deposit", "security", "code", "login", "verify"])
    if weak_only and not strong_bank:
        return "unsure", "generic keyword only; needs human check"

    if current_manual in ["yes", "no", "unsure"]:
        return current_manual, "kept existing manual label but needs review"

    return "unsure", "unclear"


def main():
    if not INPUT_PATH.exists():
        raise FileNotFoundError(f"Input file not found: {INPUT_PATH}")

    df = pd.read_csv(INPUT_PATH)

    decisions = df.apply(strict_banking_decision, axis=1)
    df["strict_banking_related"] = [d[0] for d in decisions]
    df["strict_review_reason"] = [d[1] for d in decisions]

    confirmed = df[df["strict_banking_related"] == "yes"].copy()
    recheck = df[df["strict_banking_related"] != "yes"].copy()

    confirmed.to_csv(CONFIRMED_OUTPUT, index=False)
    recheck.to_csv(RECHECK_OUTPUT, index=False)

    summary = pd.DataFrame([
        {
            "category": "total_rows",
            "count": len(df)
        },
        {
            "category": "strict_yes_confirmed_banking",
            "count": len(confirmed)
        },
        {
            "category": "strict_no_or_unsure_needs_recheck",
            "count": len(recheck)
        }
    ])

    by_source = df.groupby(["source_dataset", "strict_banking_related"]).size().reset_index(name="count")
    summary.to_csv(SUMMARY_OUTPUT, index=False)

    print("Manual review strict summary:")
    print(summary.to_string(index=False))

    print("\nBy source:")
    print(by_source.to_string(index=False))

    print(f"\nSaved confirmed banking pilot to: {CONFIRMED_OUTPUT}")
    print(f"Saved recheck file to: {RECHECK_OUTPUT}")
    print(f"Saved summary to: {SUMMARY_OUTPUT}")


if __name__ == "__main__":
    main()