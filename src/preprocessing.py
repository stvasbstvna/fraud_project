"""Normalize message tables while preserving provenance."""

from __future__ import annotations

import argparse
import hashlib
import re
from pathlib import Path

import pandas as pd

URL_RE = re.compile(r"(?i)\b(?:https?://|www\.)\S+")
SPACE_RE = re.compile(r"\s+")


def normalize_text(value: object, defang_urls: bool = True) -> str:
    text = "" if pd.isna(value) else str(value)
    if defang_urls:
        text = URL_RE.sub("[URL]", text)
    return SPACE_RE.sub(" ", text).strip()


def stable_message_id(source_id: str, source_record_id: object, text: str) -> str:
    payload = f"{source_id}\0{source_record_id}\0{text}".encode("utf-8")
    return hashlib.sha256(payload).hexdigest()[:20]


def unify_csv(path: Path, output: Path, source_id: str, text_column: str,
              label_column: str | None, subject_column: str | None,
              channel: str) -> None:
    frame = pd.read_csv(path)
    if text_column not in frame:
        raise ValueError(f"Missing text column: {text_column}")
    subject = frame[subject_column].map(normalize_text) if subject_column else ""
    body = frame[text_column].map(normalize_text)
    combined = (subject + " " + body).str.strip() if subject_column else body
    result = pd.DataFrame({
        "source_id": source_id,
        "source_record_id": frame.index.astype(str),
        "subject": subject,
        "text": combined,
        "channel": channel,
        "class_label": frame[label_column] if label_column else "unknown",
    })
    result["message_id"] = [stable_message_id(source_id, i, t) for i, t in zip(result.source_record_id, result.text)]
    result = result.drop_duplicates(subset=["text"]).reset_index(drop=True)
    output.parent.mkdir(parents=True, exist_ok=True)
    result.to_csv(output, index=False)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--source-id", required=True)
    parser.add_argument("--text-column", required=True)
    parser.add_argument("--label-column")
    parser.add_argument("--subject-column")
    parser.add_argument("--channel", choices=["sms", "email", "other_text"], required=True)
    args = parser.parse_args()
    unify_csv(args.input, args.output, args.source_id, args.text_column,
              args.label_column, args.subject_column, args.channel)


if __name__ == "__main__":
    main()
