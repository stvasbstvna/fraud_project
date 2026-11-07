"""Build the fixed SMS-only train/validation/banking-evaluation datasets.

Primary design
--------------
* Sources: SmishX and SmishTank only (email corpora are excluded).
* Banking scope: explicit bank/card/payment-service impersonation or account use.
* Banking evaluation rows are held out before model training.
* Exact and template-like duplicates are controlled before splitting.

Run from the repository root::

    python -m src.import_smishtank
    python -m src.build_final_sms_dataset
"""

from __future__ import annotations

import argparse
import hashlib
import re
from pathlib import Path

import pandas as pd
from sklearn.model_selection import StratifiedGroupKFold


DEFAULT_SMISHX_MASTER = Path("data/processed/unified_text_messages.csv")
DEFAULT_SMISHTANK = Path("data/processed/smishtank_normalized.csv")
DEFAULT_REVIEW = Path("data/review/banking_sms_review_final.xlsx")
DEFAULT_OUTPUT_DIR = Path("data/final")
DEFAULT_RESULTS_DIR = Path("results/final_dataset")

BASE_COLUMNS = [
    "id", "text", "label", "channel", "source_dataset", "source_type",
    "is_human_written", "is_ai_generated", "is_ai_rewritten",
    "is_banking_candidate", "banking_keyword", "brand_mentioned",
    "requested_action", "intent_type", "has_url", "url", "notes",
]

# Exact source-brand values treated as financial institutions/payment services.
# A separate text rule is still required when the source brand is absent.
BANKING_BRANDS = {
    value.casefold()
    for value in [
        "Bank of America", "Bank Of America", "BANK OF AMERICA", "BANKOFAMERICA",
        "Wells Fargo", "WELLS FARGO", "CITI", "Citibank", "CITIzen Bank",
        "CHASE", "Chase", "Chase Bank", "Chase Morgan", "JP Morgan",
        "Navy Federal", "Navy Federal CU", "Navy FCU", "Altura Credit Union",
        "Regions Bank", "Citizens Bank", "Bank of the West", "Alaska USA",
        "OnPoint", "RBC", "CIBC", "PNC", "Comerica", "AIB", "USBANK",
        "Union Bank", "UNIONBANK", "USAA", "Charles Schwab", "TD",
        "American Express", "Discover Card", "Visa", "VISA",
        "PayPal", "Paypal", "Zelle", "Venmo", "Cash App", "EBT", "EBT-Card",
        "Kotak Bank", "ICICI Bank",
    ]
}

BANK_BRAND_PATTERN = re.compile(
    r"(?i)\b(?:bank\s+of\s+america|bofa|b\s*o\s*a|wells\s*fargo|citibank|"
    r"citi\s*bank|chase\s*bank(?:ing)?|navy\s*federal|nfcu|regions\s*bank|"
    r"citizens\s*bank|td\s*bank|tdbank|rbc\s*bank|cibc\s*bank|pnc\s*bank|"
    r"comerica|usaa|union\s*bank|jp\s*morgan|charles\s*schwab|"
    r"american\s*express|amex|discover\s*card|credit\s*union|us\s*bank|"
    r"kotak\s*bank|icici\s*bank)\b"
)
PAYMENT_BRAND_PATTERN = re.compile(r"(?i)\b(?:paypal|zelle|venmo|cash\s*app)\b")
BANK_CONTEXT_PATTERN = re.compile(
    r"(?i)\b(?:bank(?:ing)?\s+(?:account|profile|app|application|access|login|details)|"
    r"online\s+banking|mobile\s+banking|bank\s+account|debit\s+card|credit\s+card|"
    r"prepaid\s+(?:visa\s+)?debit\s+card|routing\s+number|wire\s+transfer|"
    r"direct\s+deposit|debit\s+pin)\b"
)

# These are explicitly outside the narrow banking-smishing definition.
NON_BANKING_EXCEPTIONS = {
    "SmishTank-619": "Square marketing opt-in rather than banking/account smishing",
    "SmishTank-987": "prize message for a Visa gift card, not bank/card-account impersonation",
    "SmishTank-923": "Amazon support/fraud message without banking institution or card-account context",
}

# The source labels every SmishTank row as smishing, but this text is an
# anti-smishing warning.  Preserve the source label and exclude it from metrics.
LABEL_QUALITY_EXCLUSIONS = {
    "SmishTank-1736": "anti-smishing warning conflicts with the source phishing label",
}


def normalized_text(value: object) -> str:
    text = str(value).casefold()
    text = text.replace("hxxps://", "http://").replace("hxxp://", "http://")
    text = text.replace("[.]", ".")
    return " ".join(text.split())


def template_text(value: object) -> str:
    text = normalized_text(value)
    text = re.sub(r"(?:https?://|www\.)\S+", " [url] ", text)
    text = re.sub(r"\[email\]|\b[\w.+-]+@[\w.-]+\.[a-z]{2,}\b", " [email] ", text)
    text = re.sub(r"\[phone\]|\+?\d[\d(). -]{6,}\d", " [phone] ", text)
    text = re.sub(r"\b\d+(?:[.,]\d+)?\b", " [number] ", text)
    text = re.sub(r"[^a-z\[\] ]+", " ", text)
    return " ".join(text.split())


def short_hash(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()[:16]


def strict_banking_decision(row: pd.Series) -> tuple[str, str]:
    record_id = str(row.get("id", ""))
    if record_id in NON_BANKING_EXCEPTIONS:
        return "no", f"explicit_exclusion:{NON_BANKING_EXCEPTIONS[record_id]}"

    text = str(row.get("text", ""))
    brand = str(row.get("brand_mentioned", "")).strip().casefold()
    if brand in BANKING_BRANDS:
        return "yes", f"source_brand:{brand}"
    if BANK_BRAND_PATTERN.search(text):
        return "yes", "explicit_bank_brand_in_text"
    if PAYMENT_BRAND_PATTERN.search(text):
        return "yes", "explicit_payment_service_in_text"
    if BANK_CONTEXT_PATTERN.search(text):
        return "yes", "explicit_bank_or_card_account_context"
    return "no", "no_explicit_banking_evidence"


def load_review(path: Path) -> dict[str, str]:
    if not path.exists():
        return {}
    review = pd.read_excel(path, sheet_name="banking_sms_review")
    required = {"id", "manual_banking_label"}
    if not required.issubset(review.columns):
        raise ValueError(f"Review workbook must contain columns {sorted(required)}")
    review["manual_banking_label"] = (
        review["manual_banking_label"].astype(str).str.strip().str.casefold()
    )
    return dict(zip(review["id"].astype(str), review["manual_banking_label"]))


def standardize_sources(smishx_master: Path, smishtank_path: Path) -> pd.DataFrame:
    master = pd.read_csv(smishx_master)
    smishx = master[
        master["source_dataset"].astype(str).eq("SmishX")
        & master["channel"].astype(str).str.casefold().eq("sms")
    ].copy()
    smishtank = pd.read_csv(smishtank_path).copy()

    for frame in (smishx, smishtank):
        for column in BASE_COLUMNS:
            if column not in frame.columns:
                frame[column] = ""
        frame["text"] = frame["text"].fillna("").astype(str)
        frame["label"] = frame["label"].fillna("").astype(str).str.strip().str.casefold()
        frame["channel"] = "sms"

    combined = pd.concat([smishx[BASE_COLUMNS], smishtank[BASE_COLUMNS]], ignore_index=True)
    combined = combined[combined["label"].isin(["phishing", "legitimate", "spam"])].copy()
    combined["binary_label"] = combined["label"].eq("phishing").astype(int)
    combined["class_label"] = combined["binary_label"].map({1: "phishing", 0: "non_phishing"})
    combined["normalized_text"] = combined["text"].map(normalized_text)
    combined["template_text"] = combined["text"].map(template_text)
    combined["template_group"] = combined["template_text"].map(short_hash)
    return combined


def deduplicate(frame: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    work = frame.copy()
    work["_source_priority"] = work["source_dataset"].map({"SmishX": 0, "SmishTank": 1}).fillna(9)
    work = work.sort_values(["_source_priority", "id"], kind="stable")
    work["kept_id"] = work.groupby("normalized_text")["id"].transform("first")
    duplicates = work[work["id"].ne(work["kept_id"])].copy()
    duplicates["label_conflict"] = duplicates.groupby("normalized_text")["binary_label"].transform("nunique").gt(1)
    deduped = work.drop_duplicates("normalized_text", keep="first").copy()
    deduped = deduped.drop(columns=["_source_priority", "kept_id"])
    duplicates = duplicates.drop(columns=["_source_priority"])
    return deduped.reset_index(drop=True), duplicates.reset_index(drop=True)


def assign_banking(frame: pd.DataFrame, reviewed: dict[str, str]) -> pd.DataFrame:
    result = frame.copy()
    decisions = result.apply(strict_banking_decision, axis=1)
    result["banking_decision"] = [value[0] for value in decisions]
    result["banking_evidence"] = [value[1] for value in decisions]
    result["reviewed_in_workbook"] = result["id"].isin(reviewed)
    result["reviewed_decision"] = result["id"].map(reviewed).fillna("")

    def provenance(row: pd.Series) -> str:
        if not row["reviewed_in_workbook"]:
            return "strict_rule"
        if row["reviewed_decision"] == row["banking_decision"]:
            return "manual_rule_agreement"
        return "rule_adjudicated_manual_conflict"

    result["banking_decision_source"] = result.apply(provenance, axis=1)
    result["label_quality_flag"] = result["id"].map(LABEL_QUALITY_EXCLUSIONS).fillna("")
    return result


def assign_splits(frame: pd.DataFrame) -> pd.DataFrame:
    result = frame.copy()
    banking_test_mask = result["banking_decision"].eq("yes") & result["label_quality_flag"].eq("")
    result["split"] = "banking_test"

    development = result[~banking_test_mask].copy()
    splitter = StratifiedGroupKFold(n_splits=5, shuffle=True, random_state=42)
    train_idx, validation_idx = next(
        splitter.split(
            development,
            development["binary_label"],
            groups=development["template_group"],
        )
    )
    result.loc[development.iloc[train_idx].index, "split"] = "train"
    result.loc[development.iloc[validation_idx].index, "split"] = "validation"

    # Label-quality exclusions are not used in any model fit or metric.
    result.loc[result["label_quality_flag"].ne(""), "split"] = "excluded_label_quality"
    return result


def build_summary(master: pd.DataFrame, duplicates: pd.DataFrame) -> pd.DataFrame:
    records: list[dict[str, object]] = []

    def add(section: str, key: str, value: object) -> None:
        records.append({"section": section, "key": key, "value": value})

    add("corpus", "rows_after_deduplication", len(master))
    add("corpus", "duplicate_rows_removed", len(duplicates))
    add("corpus", "template_groups", master["template_group"].nunique())
    for source, count in master["source_dataset"].value_counts().sort_index().items():
        add("source", str(source), int(count))
    for split, count in master["split"].value_counts().sort_index().items():
        add("split", str(split), int(count))
    for (split, label), count in master.groupby(["split", "class_label"]).size().items():
        add("split_class", f"{split}:{label}", int(count))
    for (source, decision), count in master.groupby(["source_dataset", "banking_decision"]).size().items():
        add("banking_by_source", f"{source}:{decision}", int(count))
    for method, count in master["banking_decision_source"].value_counts().sort_index().items():
        add("decision_provenance", str(method), int(count))
    return pd.DataFrame(records)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--smishx-master", type=Path, default=DEFAULT_SMISHX_MASTER)
    parser.add_argument("--smishtank", type=Path, default=DEFAULT_SMISHTANK)
    parser.add_argument("--review", type=Path, default=DEFAULT_REVIEW)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--results-dir", type=Path, default=DEFAULT_RESULTS_DIR)
    args = parser.parse_args()

    frame = standardize_sources(args.smishx_master, args.smishtank)
    deduped, duplicates = deduplicate(frame)
    reviewed = load_review(args.review)
    master = assign_splits(assign_banking(deduped, reviewed))

    args.output_dir.mkdir(parents=True, exist_ok=True)
    args.results_dir.mkdir(parents=True, exist_ok=True)

    output_columns = [
        *BASE_COLUMNS, "binary_label", "class_label", "banking_decision",
        "banking_evidence", "reviewed_in_workbook", "reviewed_decision",
        "banking_decision_source", "label_quality_flag", "template_group", "split",
    ]
    master[output_columns].to_csv(
        args.output_dir / "sms_master_with_splits.csv", index=False, lineterminator="\n"
    )
    for split, filename in [
        ("train", "train_sms.csv"),
        ("validation", "validation_sms.csv"),
        ("banking_test", "banking_original_test.csv"),
    ]:
        master[master["split"].eq(split)][output_columns].to_csv(
            args.output_dir / filename, index=False, lineterminator="\n"
        )

    audit_columns = [
        "id", "source_dataset", "text", "label", "binary_label",
        "banking_decision", "banking_evidence", "reviewed_in_workbook",
        "reviewed_decision", "banking_decision_source", "label_quality_flag", "split",
    ]
    master[audit_columns].to_csv(
        args.output_dir / "banking_decision_audit.csv", index=False, lineterminator="\n"
    )
    duplicates.to_csv(
        args.results_dir / "cross_source_and_exact_duplicates_removed.csv",
        index=False,
        lineterminator="\n",
    )
    summary = build_summary(master, duplicates)
    summary.to_csv(args.output_dir / "dataset_summary.csv", index=False, lineterminator="\n")

    print(summary.to_string(index=False))
    print(f"\nSaved final datasets to: {args.output_dir}")


if __name__ == "__main__":
    main()
