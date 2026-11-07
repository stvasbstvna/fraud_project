from pathlib import Path
import re

import pandas as pd


UNIFIED_PATH = Path("data/processed/unified_text_messages.csv")
SMISHTANK_PATH = Path("data/processed/smishtank_normalized.csv")

OUTPUT_PATH = Path("data/processed/sms_master_v2.csv")
REVIEW_PATH = Path("data/review/banking_sms_review.csv")
CROSS_DUPLICATES_PATH = Path(
    "results/smishtank_smishx_cross_source_duplicates.csv"
)


BANK_BRAND_RE = re.compile(
    r"\b("
    r"bank of america|bofa|wells fargo|citi|citibank|"
    r"chase|regions bank|citizens bank|usaa|pnc|truist|"
    r"capital one|hsbc|barclays|santander|td bank|"
    r"american express|amex|discover|navy federal|"
    r"woodforest|fifth third|huntington|m&t bank|"
    r"keybank|first citizens|ally bank"
    r")\b",
    flags=re.IGNORECASE,
)

STRONG_BANKING_RE = re.compile(
    r"\b("
    r"bank account|banking account|online banking|mobile banking|"
    r"debit card|credit card|atm card|checking account|"
    r"savings account|bank transfer|wire transfer|"
    r"card locked|card blocked|card suspended|"
    r"unauthorized transaction|fraud alert|bank alert"
    r")\b",
    flags=re.IGNORECASE,
)


def normalized_key(text: str) -> str:
    text = str(text or "").lower()

    # Normalize defanged and ordinary URL notation.
    text = text.replace("hxxps://", "https://")
    text = text.replace("hxxp://", "http://")
    text = text.replace("[.]", ".")

    # Normalize placeholders.
    text = re.sub(r"\[\[?phone\]?\]", "[phone]", text)

    # Remove spacing and punctuation differences.
    text = re.sub(r"[^\w\s]", " ", text)
    text = re.sub(r"\s+", " ", text)

    return text.strip()


def standardize_boolean(value) -> str:
    value = str(value).strip().lower()

    if value in {"true", "1", "yes"}:
        return "true"

    if value in {"false", "0", "no"}:
        return "false"

    return "unknown"


def high_precision_banking_candidate(row) -> bool:
    text = str(row.get("text", ""))
    brand = str(row.get("brand_mentioned", ""))

    return bool(
        BANK_BRAND_RE.search(brand)
        or BANK_BRAND_RE.search(text)
        or STRONG_BANKING_RE.search(text)
    )


def main() -> None:
    existing = pd.read_csv(
        UNIFIED_PATH,
        dtype=str,
        keep_default_na=False,
    )

    smishx = existing[
        existing["source_dataset"].eq("SmishX")
    ].copy()

    smishtank = pd.read_csv(
        SMISHTANK_PATH,
        dtype=str,
        keep_default_na=False,
    )

    print(f"SmishX rows: {len(smishx)}")
    print(f"Normalized SmishTank rows: {len(smishtank)}")

    # Standardize shared fields.
    for frame in (smishx, smishtank):
        frame["channel"] = "sms"
        frame["text"] = frame["text"].astype(str).str.strip()
        frame["deduplication_key"] = frame["text"].apply(
            normalized_key
        )

        for column in (
            "is_human_written",
            "is_ai_generated",
            "is_ai_rewritten",
        ):
            if column not in frame.columns:
                frame[column] = "unknown"

            frame[column] = frame[column].apply(
                standardize_boolean
            )

    # Find overlaps between sources before removing them.
    cross_duplicates = smishtank[
        smishtank["deduplication_key"].isin(
            set(smishx["deduplication_key"])
        )
    ].copy()

    # Preserve the existing SmishX version when the same text exists
    # in both datasets.
    smishtank_unique = smishtank[
        ~smishtank["deduplication_key"].isin(
            set(smishx["deduplication_key"])
        )
    ].copy()

    all_columns = sorted(
        set(smishx.columns).union(smishtank_unique.columns)
    )

    smishx = smishx.reindex(columns=all_columns, fill_value="")
    smishtank_unique = smishtank_unique.reindex(
        columns=all_columns,
        fill_value="",
    )

    combined = pd.concat(
        [smishx, smishtank_unique],
        ignore_index=True,
    )

    # Final protection against remaining duplicates.
    combined = combined.drop_duplicates(
        subset="deduplication_key",
        keep="first",
    ).copy()

    combined["high_precision_banking_candidate"] = combined.apply(
        high_precision_banking_candidate,
        axis=1,
    )

    combined["banking_verified"] = combined.apply(
        lambda row: (
            "pending_manual_review"
            if row["high_precision_banking_candidate"]
            else "not_banking"
        ),
        axis=1,
    )

    # Create a smaller manual review queue.
    review = combined[
        combined["high_precision_banking_candidate"]
    ].copy()

    review_columns = [
        "id",
        "source_dataset",
        "text",
        "label",
        "brand_mentioned",
        "intent_type",
        "requested_action",
        "has_url",
        "url",
        "banking_verified",
    ]

    for column in review_columns:
        if column not in review.columns:
            review[column] = ""

    review = review[review_columns].copy()

    review["manual_banking_label"] = ""
    review["manual_intent_type"] = ""
    review["review_notes"] = ""

    combined = combined.drop(
        columns=["deduplication_key"]
    )

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    REVIEW_PATH.parent.mkdir(parents=True, exist_ok=True)
    CROSS_DUPLICATES_PATH.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    combined.to_csv(
        OUTPUT_PATH,
        index=False,
        encoding="utf-8",
    )

    review.to_csv(
        REVIEW_PATH,
        index=False,
        encoding="utf-8-sig",
    )

    cross_duplicates.to_csv(
        CROSS_DUPLICATES_PATH,
        index=False,
        encoding="utf-8",
    )

    print(
        f"Cross-source duplicates removed: "
        f"{len(cross_duplicates)}"
    )
    print(f"Final unique SMS rows: {len(combined)}")
    print(f"Manual banking review rows: {len(review)}")

    print("\nSource distribution:")
    print(
        combined["source_dataset"]
        .value_counts()
        .to_string()
    )

    print("\nLabel distribution:")
    print(
        combined["label"]
        .value_counts()
        .to_string()
    )

    print(f"\nSaved SMS master: {OUTPUT_PATH}")
    print(f"Saved review queue: {REVIEW_PATH}")
    print(f"Saved cross-source duplicates: {CROSS_DUPLICATES_PATH}")


if __name__ == "__main__":
    main()