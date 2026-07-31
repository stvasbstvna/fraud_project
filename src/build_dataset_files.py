"""Build the committed, license-cleared standardized dataset files.

This script does not download data. Pass local paths to the SmishX dataset and
the human/LLM CSV files from the cross-model package described in data docs.
"""

from __future__ import annotations

import argparse
import hashlib
import re
from pathlib import Path

import pandas as pd

SCHEMA = [
    "id", "text", "label", "channel", "source_dataset", "source_type",
    "is_human_written", "is_ai_generated", "is_ai_rewritten",
    "is_banking_candidate", "banking_keyword", "brand_mentioned",
    "requested_action", "intent_type", "has_url", "url", "notes",
]

MANUAL_SCHEMA = [
    "id", "text", "label", "channel", "source_dataset", "banking_keyword",
    "is_banking_candidate", "manual_banking_related", "brand_mentioned",
    "requested_action", "intent_type", "manual_notes",
]

BANKING_KEYWORDS = [
    "bank", "account", "card", "credit", "debit", "payment", "transaction",
    "transfer", "deposit", "withdrawal", "balance", "fraud", "security",
    "suspicious", "locked", "suspended", "verify", "login", "password",
    "OTP", "code", "PayPal", "Zelle", "Venmo", "Cash App", "Chase",
    "Wells Fargo", "Bank of America", "Capital One", "Citi", "Discover",
    "American Express", "Stripe",
]

BRANDS = [
    "PayPal", "Zelle", "Venmo", "Cash App", "Chase", "Wells Fargo",
    "Bank of America", "Capital One", "Citi", "Discover",
    "American Express", "Stripe",
]

URL_RE = re.compile(r"(?i)(?:https?://|www\.)[^\s<>'\"]+")
EMAIL_RE = re.compile(r"(?i)(?<![\w.+-])[\w.+-]+@[\w.-]+\.[a-z]{2,}(?![\w.-])")
PHONE_RE = re.compile(r"(?<!\w)(?:\+?\d[\d(). -]{6,}\d)(?!\w)")

ACTION_RULES = [
    ("provide_credentials", "credential_theft", re.compile(r"(?i)\b(?:provide|enter|send|share|confirm)\b.{0,45}\b(?:password|login|otp|code|credential|account details|card details)\b")),
    ("transfer_money", "financial_transfer", re.compile(r"(?i)\b(?:transfer|send|pay|deposit)\b.{0,35}\b(?:money|funds|payment|fee|balance|account)\b")),
    ("verify_account", "account_verification", re.compile(r"(?i)\b(?:verify|confirm|validate|unlock)\b.{0,35}\b(?:account|identity|transaction|payment|card|login)\b")),
    ("click_link", "link_navigation", re.compile(r"(?i)\b(?:click|tap|visit|follow|open)\b.{0,35}\b(?:link|url|website|page)\b")),
    ("call_phone", "contact_request", re.compile(r"(?i)\b(?:call|phone|dial)\b")),
    ("reply", "contact_request", re.compile(r"(?i)\b(?:reply|respond|email us)\b")),
    ("download_attachment", "attachment_action", re.compile(r"(?i)\b(?:download|open|view)\b.{0,35}\b(?:attachment|invoice|document|file)\b")),
]


def stable_id(source: str, row_number: int, text: str) -> str:
    digest = hashlib.sha256(f"{source}\0{row_number}\0{text}".encode("utf-8")).hexdigest()
    return f"{source}-{digest[:16]}"


def keyword_matches(text: str, terms: list[str]) -> list[str]:
    matches = []
    for term in terms:
        pattern = rf"(?i)(?<!\w){re.escape(term)}(?!\w)"
        if re.search(pattern, text):
            matches.append(term)
    return matches


def defang_url(value: str) -> str:
    return re.sub(r"(?i)http", "hxxp", value).replace(".", "[.]")


def extract_urls(text: str) -> list[str]:
    return [match.rstrip(".,;:!?)\"]}'") for match in URL_RE.findall(text)]


def defang_text(text: str) -> str:
    text = URL_RE.sub(lambda match: defang_url(match.group(0)), text)
    text = EMAIL_RE.sub("[EMAIL]", text)
    return PHONE_RE.sub("[PHONE]", text)


def sanitize_url(value: str) -> str:
    value = defang_url(value)
    value = EMAIL_RE.sub("[EMAIL]", value)
    return PHONE_RE.sub("[PHONE]", value)


def infer_action(text: str) -> tuple[str, str]:
    for action, intent, pattern in ACTION_RULES:
        if pattern.search(text):
            return action, intent
    return "unknown", "unknown"


def make_row(*, source: str, row_number: int, text: str, label: str,
             channel: str, source_type: str, is_human: str, is_ai: str,
             is_rewrite: str, notes: str) -> dict[str, object]:
    clean = " ".join(str(text).split())
    keywords = keyword_matches(clean, BANKING_KEYWORDS)
    brands = keyword_matches(clean, BRANDS)
    urls = extract_urls(clean)
    action, intent = infer_action(clean)
    return {
        "id": stable_id(source, row_number, clean),
        "text": defang_text(clean),
        "label": label,
        "channel": channel,
        "source_dataset": source,
        "source_type": source_type,
        "is_human_written": is_human,
        "is_ai_generated": is_ai,
        "is_ai_rewritten": is_rewrite,
        "is_banking_candidate": bool(keywords),
        "banking_keyword": "|".join(keywords),
        "brand_mentioned": "|".join(brands),
        "requested_action": action,
        "intent_type": intent,
        "has_url": bool(urls),
        "url": "|".join(sanitize_url(url) for url in urls),
        "notes": notes,
    }


def load_smishx(path: Path) -> list[dict[str, object]]:
    frame = pd.read_csv(path)
    label_map = {"smishing": "phishing", "legitimate": "legitimate", "spam": "spam"}
    rows = []
    for index, row in frame.iterrows():
        original_label = str(row["label"]).strip().lower()
        notes = f"original_label={original_label};if_URL={row.get('if_URL', 'unknown')};authorship_not_provided"
        rows.append(make_row(
            source="SmishX", row_number=index, text=row["SMS"],
            label=label_map.get(original_label, "unknown"), channel="sms",
            source_type="public_dataset_relabelled", is_human="unknown",
            is_ai="unknown", is_rewrite="unknown", notes=notes,
        ))
    return rows


def load_cross_model_human(path: Path) -> list[dict[str, object]]:
    frame = pd.read_csv(path)
    rows = []
    for index, row in frame.iterrows():
        notes = f"upstream_source={row.get('source', 'unknown')};package_authorship=human;all_rows_phishing"
        rows.append(make_row(
            source="cross_model_human", row_number=index, text=row["text"],
            label="phishing", channel="email", source_type="human_phishing_corpus",
            is_human="true", is_ai="false", is_rewrite="false", notes=notes,
        ))
    return rows


def load_cross_model_llm(path: Path) -> list[dict[str, object]]:
    frame = pd.read_csv(path)
    rows = []
    for index, row in frame.iterrows():
        model = row.get("model", row.get("source", "unknown"))
        category = row.get("category", "unknown")
        notes = f"generator={model};generation_category={category};package_authorship=LLM;all_rows_phishing;not_paired_rewrite"
        rows.append(make_row(
            source="cross_model_llm", row_number=index, text=row["text"],
            label="phishing", channel="email", source_type="llm_generated_phishing_corpus",
            is_human="false", is_ai="true", is_rewrite="false", notes=notes,
        ))
    return rows


def write_outputs(frame: pd.DataFrame, output_dir: Path) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    frame = frame[SCHEMA]
    candidates = frame[frame["is_banking_candidate"]].copy()
    manual = candidates[[
        "id", "text", "label", "channel", "source_dataset", "banking_keyword",
        "is_banking_candidate", "brand_mentioned", "requested_action", "intent_type",
    ]].copy()
    manual.insert(7, "manual_banking_related", "")
    manual["manual_notes"] = ""
    manual = manual[MANUAL_SCHEMA]

    outputs = {
        "unified_text_messages.csv": frame,
        "banking_candidates.csv": candidates,
        "banking_manual_review.csv": manual,
        "banking_human_written.csv": candidates[candidates["is_human_written"].eq("true")],
        "banking_ai_generated.csv": candidates[candidates["is_ai_generated"].eq("true")],
        "banking_ai_rewritten.csv": candidates[candidates["is_ai_rewritten"].eq("true")],
    }
    for name, data in outputs.items():
        data.to_csv(output_dir / name, index=False, lineterminator="\n")
        print(f"{name}: {len(data)} rows")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--smishx", type=Path, required=True)
    parser.add_argument("--cross-model-human", type=Path, required=True)
    parser.add_argument("--cross-model-llm", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, default=Path("data/processed"))
    args = parser.parse_args()
    rows = load_smishx(args.smishx)
    rows += load_cross_model_human(args.cross_model_human)
    rows += load_cross_model_llm(args.cross_model_llm)
    write_outputs(pd.DataFrame(rows), args.output_dir)


if __name__ == "__main__":
    main()
