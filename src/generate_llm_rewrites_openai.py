"""Generate resumable, structured, defanged rewrites with the OpenAI Responses API."""

from __future__ import annotations

import argparse
from collections import Counter
import json
import os
import re
import time
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd
from dotenv import load_dotenv


DEFAULT_INPUT = Path("data/rewrite_experiment/rewrite_pairs.csv")
DEFAULT_MODEL = "gpt-5.4-mini-2026-03-17"
LIVE_URL = re.compile(r"https?://", re.IGNORECASE)
PLACEHOLDER = re.compile(r"\[[A-Z][A-Z0-9_ -]*\]")
DEFANGED_URL = re.compile(r"(?i)hxxps?://[^\s<>'\"]+")
PHONE = re.compile(r"(?<!\w)(?:\+?\d[\d(). -]{6,}\d)(?!\w)")
EMAIL = re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b")

INSTRUCTIONS = """You are transforming a DEFANGED SMS example for a controlled academic robustness study.
Rewrite it once in natural contemporary SMS language. Preserve the same high-level situation,
true class, semantic intent, and requested-action category. Keep every bracketed placeholder
exactly as written. Keep any defanged destination non-operational. Do not add a real URL, phone
number, email address, personal data, credential request, payment instruction, targeting detail,
new urgency, threat, reward, or persuasive strategy. Do not optimize against a detector. Do not
infer or discuss detector features. Return only the requested structured object."""

SCHEMA = {
    "type": "object",
    "properties": {
        "pair_id": {"type": "string"},
        "original_id": {"type": "string"},
        "rewrite_text": {"type": "string"},
        "semantic_intent_preserved": {"type": "boolean"},
        "requested_action_preserved": {"type": "boolean"},
        "label_preserved": {"type": "boolean"},
        "operational_detail_added": {"type": "boolean"},
    },
    "required": [
        "pair_id", "original_id", "rewrite_text", "semantic_intent_preserved",
        "requested_action_preserved", "label_preserved",
        "operational_detail_added",
    ],
    "additionalProperties": False,
}


def row_input(row: pd.Series) -> str:
    return (
        f"Pair ID (return unchanged): {row['pair_id']}\n"
        f"Original ID (return unchanged): {row['original_id']}\n"
        f"True class: {row['true_label']}\n"
        f"Intent category: {row['intent_type']}\n"
        f"Requested-action category: {row['requested_action']}\n"
        f"DEFANGED source text:\n{row['original_text']}"
    )


def local_safety_check(
    original: str,
    rewritten: str,
    parsed: dict,
    expected_pair_id: str | None = None,
    expected_original_id: str | None = None,
) -> tuple[bool, str]:
    reasons = []
    if not rewritten.strip():
        reasons.append("empty rewrite")
    if rewritten.strip() == original.strip():
        reasons.append("rewrite equals original")
    if LIVE_URL.search(rewritten):
        reasons.append("live URL scheme detected")
    missing = list((Counter(PLACEHOLDER.findall(original)) - Counter(PLACEHOLDER.findall(rewritten))).elements())
    if missing:
        reasons.append(f"missing placeholders: {missing}")
    missing_defanged = [value for value in DEFANGED_URL.findall(original) if value not in rewritten]
    if missing_defanged:
        reasons.append("defanged URL changed or removed")
    new_phones = set(PHONE.findall(rewritten)) - set(PHONE.findall(original))
    if new_phones:
        reasons.append("new phone-like value detected")
    new_emails = set(EMAIL.findall(rewritten)) - set(EMAIL.findall(original))
    if new_emails:
        reasons.append("new email address detected")
    if expected_pair_id is not None and parsed.get("pair_id") != expected_pair_id:
        reasons.append("pair_id changed")
    if expected_original_id is not None and parsed.get("original_id") != expected_original_id:
        reasons.append("original_id changed")
    if parsed.get("operational_detail_added") is not False:
        reasons.append("model reported operational detail")
    for field in ("semantic_intent_preserved", "requested_action_preserved", "label_preserved"):
        if parsed.get(field) is not True:
            reasons.append(f"model reported {field}=false")
    return not reasons, "; ".join(reasons)


def generation_counts(frame: pd.DataFrame) -> dict[str, int]:
    rewrites = frame[frame["condition"].eq("T1_llm_neutral_rewrite")]
    status = rewrites["generation_status"].astype(str)
    return {
        "completed": int(status.eq("completed").sum()),
        "rejected": int(status.eq("rejected_safety_check").sum()),
        "pending": int(status.eq("pending").sum()),
        "total": int(len(rewrites)),
    }


def select_generation_targets(
    frame: pd.DataFrame,
    *,
    retry_rejected: bool = False,
    max_attempts: int = 2,
    limit: int | None = None,
) -> pd.DataFrame:
    if max_attempts < 1:
        raise ValueError("max_attempts must be at least 1")
    rewrite_mask = frame["condition"].eq("T1_llm_neutral_rewrite")
    pending = frame[rewrite_mask & frame["generation_status"].eq("pending")]
    parts = [pending]
    if retry_rejected:
        rejected = frame[
            rewrite_mask
            & frame["generation_status"].eq("rejected_safety_check")
            & frame["generation_attempts"].lt(max_attempts)
        ]
        parts.append(rejected)
    target = pd.concat(parts)
    if limit is not None:
        target = target.head(limit)
    return target


def _retry_time(error: Exception) -> str:
    retry_after = getattr(error, "retry_after", None)
    response = getattr(error, "response", None)
    headers = getattr(response, "headers", None)
    if retry_after is None and headers is not None:
        retry_after = headers.get("retry-after") or headers.get("x-ratelimit-reset-requests")
    return str(retry_after) if retry_after not in (None, "") else "not provided"


def run_generation(
    frame: pd.DataFrame,
    *,
    input_path: Path,
    client,
    rate_limit_error: type[Exception],
    model: str,
    retry_rejected: bool = False,
    max_attempts: int = 2,
    limit: int | None = None,
    pause_seconds: float = 0.25,
) -> bool:
    target = select_generation_targets(
        frame,
        retry_rejected=retry_rejected,
        max_attempts=max_attempts,
        limit=limit,
    )
    for idx, row in target.iterrows():
        try:
            response = client.responses.create(
                model=model,
                reasoning={"effort": "none"},
                instructions=INSTRUCTIONS,
                input=row_input(row),
                text={
                    "format": {
                        "type": "json_schema",
                        "name": "defanged_sms_rewrite",
                        "strict": True,
                        "schema": SCHEMA,
                    }
                },
            )
        except rate_limit_error as error:
            message = " ".join(str(error).split())[:300]
            print(f"Rate limit: {message}. Retry time: {_retry_time(error)}.")
            counts = generation_counts(frame)
            print(
                "Current counts: "
                f"completed={counts['completed']}, rejected={counts['rejected']}, "
                f"pending={counts['pending']}"
            )
            return False

        parsed = json.loads(response.output_text)
        rewritten = parsed["rewrite_text"].strip()
        safe, note = local_safety_check(
            str(row["original_text"]), rewritten, parsed,
            expected_pair_id=str(row["pair_id"]),
            expected_original_id=str(row["original_id"]),
        )

        frame.at[idx, "text"] = rewritten
        frame.at[idx, "generator_model"] = model
        frame.at[idx, "response_id"] = response.id
        frame.at[idx, "generated_at_utc"] = datetime.now(timezone.utc).isoformat()
        frame.at[idx, "generation_status"] = "completed" if safe else "rejected_safety_check"
        frame.at[idx, "generation_attempts"] = int(row.get("generation_attempts", 0)) + 1
        frame.at[idx, "rejection_reason"] = note if not safe else ""
        frame.at[idx, "safety_check_passed"] = bool(safe)
        frame.at[idx, "semantic_intent_preserved"] = str(parsed["semantic_intent_preserved"]).lower()
        frame.at[idx, "requested_action_preserved"] = str(parsed["requested_action_preserved"]).lower()
        frame.at[idx, "label_preserved"] = str(parsed["label_preserved"]).lower()
        frame.at[idx, "human_review_status"] = "pending"
        frame.at[idx, "review_notes"] = note
        frame.to_csv(input_path, index=False, lineterminator="\n")
        print(f"{row['pair_id']}: {'completed' if safe else 'rejected'}")
        time.sleep(pause_seconds)
    return True


def main() -> None:
    load_dotenv()
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT)
    parser.add_argument("--model", default=os.getenv("REWRITE_MODEL", DEFAULT_MODEL))
    parser.add_argument("--limit", type=int, default=None, help="Generate at most N pending rewrites")
    parser.add_argument("--pause-seconds", type=float, default=0.25)
    parser.add_argument(
        "--retry-rejected", action="store_true",
        help="After pending rows, retry rejected safety-check rows below --max-attempts",
    )
    parser.add_argument(
        "--max-attempts", type=int, default=2,
        help="Maximum API attempts allowed for rejected rows (default: 2)",
    )
    args = parser.parse_args()

    if args.model != DEFAULT_MODEL:
        raise SystemExit(f"REWRITE_MODEL must be exactly {DEFAULT_MODEL}; refusing {args.model}")
    if "OPENAI_API_KEY" not in os.environ:
        raise SystemExit("OPENAI_API_KEY is not set. Set it locally; never commit it.")
    try:
        from openai import OpenAI, RateLimitError
    except ImportError as exc:
        raise SystemExit("Install dependencies with: python -m pip install -r requirements.txt") from exc

    frame = pd.read_csv(args.input, keep_default_na=False)
    for column, default in (("generation_attempts", 0), ("rejection_reason", "")):
        if column not in frame.columns:
            frame[column] = default
    frame["generation_attempts"] = pd.to_numeric(frame["generation_attempts"], errors="coerce").fillna(0).astype(int)
    client = OpenAI()
    finished = run_generation(
        frame,
        input_path=args.input,
        client=client,
        rate_limit_error=RateLimitError,
        model=args.model,
        retry_rejected=args.retry_rejected,
        max_attempts=args.max_attempts,
        limit=args.limit,
        pause_seconds=args.pause_seconds,
    )
    if not finished:
        return
    counts = generation_counts(frame)
    print(f"Completed safe rewrites: {counts['completed']} / {counts['total']}")
    print("Manual review is still required before final analysis.")


if __name__ == "__main__":
    main()
