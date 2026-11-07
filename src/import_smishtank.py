"""Normalize the locally supplied SmishTank CSV into the project schema.

The raw file is intentionally git-ignored.  Rebuild with::

    python -m src.import_smishtank
"""

from __future__ import annotations

import argparse
import re
from pathlib import Path

import pandas as pd


DEFAULT_INPUT = Path("data/raw/smishtank/analysisdataset.csv")
DEFAULT_OUTPUT = Path("data/processed/smishtank_normalized.csv")
DEFAULT_DUPLICATES = Path("results/smishtank_duplicate_rows.csv")

URL_RE = re.compile(
    r"(?i)(?:https?://|hxxps?://|www\.)[^\s<>'\"]+|"
    r"(?<![@\w])(?:[a-z0-9-]+\.)+(?:com|net|org|info|co|io|me|us|app|link|live|site|ml|ga|vip)(?:/[^\s<>'\"]*)?"
)
EMAIL_RE = re.compile(r"(?i)(?<![\w.+-])[\w.+-]+@[\w.-]+\.[a-z]{2,}(?![\w.-])")
PHONE_RE = re.compile(r"(?<!\w)(?:\+?\d[\d(). -]{6,}\d)(?!\w)")


def clean_text(value: object) -> str:
    return " ".join(str(value).replace("\x00", " ").split())


def defang_url(value: str) -> str:
    value = re.sub(r"(?i)^https", "hxxps", value)
    value = re.sub(r"(?i)^http", "hxxp", value)
    return value.replace(".", "[.]")


def sanitize_text(text: str) -> str:
    text = URL_RE.sub(lambda match: defang_url(match.group(0).rstrip(".,;:!?)\"]}'")), text)
    text = EMAIL_RE.sub("[EMAIL]", text)
    return PHONE_RE.sub("[PHONE]", text)


def extract_urls(text: str) -> list[str]:
    return [defang_url(match.group(0).rstrip(".,;:!?)\"]}'")) for match in URL_RE.finditer(text)]


def infer_requested_action(text: str) -> str:
    lower = text.lower()
    rules = [
        ("follow_link", r"\b(?:click|tap|visit|follow|open|login|log in)\b"),
        ("reply", r"\b(?:reply|respond|text)\b"),
        ("call_phone", r"\b(?:call|dial|phone)\b"),
        ("provide_credentials", r"\b(?:password|pin|otp|cvv|credentials?)\b"),
        ("make_payment", r"\b(?:pay|payment|transfer|send money)\b"),
    ]
    for action, pattern in rules:
        if re.search(pattern, lower):
            return action
    return "unknown"


def read_raw(path: Path) -> pd.DataFrame:
    errors: list[str] = []
    for encoding in ("utf-8", "cp1252", "latin1"):
        try:
            frame = pd.read_csv(path, encoding=encoding)
            frame.attrs["source_encoding"] = encoding
            return frame
        except UnicodeDecodeError as exc:
            errors.append(f"{encoding}: {exc}")
    raise UnicodeError("Unable to decode SmishTank CSV: " + " | ".join(errors))


def normalize(path: Path) -> tuple[pd.DataFrame, pd.DataFrame]:
    raw = read_raw(path)
    required = {"messageid", "MainText", "Fulltext", "Brand", "Message Categories"}
    missing = sorted(required.difference(raw.columns))
    if missing:
        raise ValueError(f"SmishTank input is missing columns: {missing}")

    rows: list[dict[str, object]] = []
    for _, row in raw.iterrows():
        source_text = row.get("MainText")
        if pd.isna(source_text) or not str(source_text).strip():
            source_text = row.get("Fulltext", "")
        clean = clean_text(source_text)
        urls = extract_urls(clean)
        message_id = str(row["messageid"]).strip()
        rows.append(
            {
                "id": f"SmishTank-{message_id}",
                "text": sanitize_text(clean),
                "label": "phishing",
                "channel": "sms",
                "source_dataset": "SmishTank",
                "source_type": "community_reported_smishing_dataset",
                "is_human_written": "unknown",
                "is_ai_generated": "unknown",
                "is_ai_rewritten": "false",
                "is_banking_candidate": False,
                "banking_keyword": "",
                "brand_mentioned": clean_text(row.get("Brand", "")) if not pd.isna(row.get("Brand")) else "",
                "requested_action": infer_requested_action(clean),
                "intent_type": clean_text(row.get("Message Categories", "")) if not pd.isna(row.get("Message Categories")) else "unknown",
                "has_url": bool(urls),
                "url": "|".join(urls),
                "notes": (
                    f"source_messageid={message_id};"
                    f"source_encoding={raw.attrs.get('source_encoding', 'unknown')};"
                    "source_label=community_reported_smishing;authorship_not_provided"
                ),
            }
        )

    frame = pd.DataFrame(rows)
    frame["_normalized_text"] = (
        frame["text"].str.lower().str.replace(r"\s+", " ", regex=True).str.strip()
    )
    duplicates = frame[frame.duplicated("_normalized_text", keep="first")].copy()
    frame = frame.drop_duplicates("_normalized_text", keep="first").drop(columns="_normalized_text")
    duplicates = duplicates.drop(columns="_normalized_text")
    return frame.reset_index(drop=True), duplicates.reset_index(drop=True)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--duplicates-output", type=Path, default=DEFAULT_DUPLICATES)
    args = parser.parse_args()

    normalized, duplicates = normalize(args.input)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.duplicates_output.parent.mkdir(parents=True, exist_ok=True)
    normalized.to_csv(args.output, index=False, lineterminator="\n")
    duplicates.to_csv(args.duplicates_output, index=False, lineterminator="\n")

    print(f"Raw SmishTank rows: {len(normalized) + len(duplicates)}")
    print(f"Exact normalized duplicates removed: {len(duplicates)}")
    print(f"Final normalized rows: {len(normalized)}")
    print(f"Saved: {args.output}")
    print(f"Saved duplicates: {args.duplicates_output}")


if __name__ == "__main__":
    main()
