"""Build deterministic offline triage for Benchmark v1 human rewrite review.

Triage prioritizes reviewer attention. It is not human review and cannot
establish semantic preservation, requested-action preservation, or naturalness.
No detector output is read or written.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import tempfile
from collections import Counter
from pathlib import Path

import pandas as pd


DEFAULT_SOURCE = Path("data/rewrite_experiment/rewrite_pairs.csv")
DEFAULT_QUEUE = Path("data/rewrite_experiment/human_review/review_triage_queue.csv")
DEFAULT_JSON = Path("results/rewrite_experiment/review_triage_summary.json")
DEFAULT_MARKDOWN = Path("results/rewrite_experiment/review_triage_summary.md")
ORIGINAL = "T0_original"
REWRITE = "T1_llm_neutral_rewrite"
LENGTH_RATIO_MIN = 0.55
LENGTH_RATIO_MAX = 1.80
TOKEN_OVERLAP_MIN = 0.45

WORD_RE = re.compile(r"[A-Za-z0-9]+(?:['’-][A-Za-z0-9]+)?", re.UNICODE)
LIVE_URL_RE = re.compile(r"(?i)\bhttps?://[^\s<>]+")
EMAIL_RE = re.compile(r"(?i)\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b")
PHONE_RE = re.compile(r"(?<!\w)(?:\+?\d[\d ()-]{5,}\d)(?!\w)")
AMOUNT_RE = re.compile(
    r"(?i)(?:[$£€]\s*\d+(?:[.,]\d+)*|\d+(?:[.,]\d+)*\s*(?:usd|gbp|eur|dollars?|pounds?|euros?))"
)
URLISH_RE = re.compile(
    r"(?i)\b(?:https?://|hxxps?://)?(?:[a-z0-9-]+(?:\[\.\]|\(dot\)|\.)+)+[a-z]{2,}(?:[/\\][^\s]*)?"
)
DOMAIN_RE = re.compile(
    r"(?i)\b(?:[a-z0-9-]+(?:\[\.\]|\(dot\)|\.)+)+[a-z]{2,}\b"
)
URL_PLACEHOLDER_RE = re.compile(r"(?i)\[(?:URL|DEFANGED(?:-[A-Z]+)*-LINK|LINK)\]")
ENTITY_STOPWORDS = {
    "a", "an", "and", "at", "bank", "banking", "customer", "dear", "for", "from",
    "hello", "hi", "i", "in", "it", "message", "notice", "official", "please",
    "service", "sms", "the", "this", "to", "we", "your",
}
COMMON_TLDS = {
    "app", "biz", "ca", "co", "com", "edu", "gov", "info", "io", "me",
    "net", "org", "uk", "us",
}

QUEUE_COLUMNS = [
    "pair_id", "original_text", "rewrite_text", "exact_match_with_original",
    "normalized_text_match", "original_length", "rewrite_length", "length_ratio",
    "token_overlap_ratio", "defanged_url_preserved", "newly_introduced_url",
    "newly_introduced_domain", "newly_introduced_email",
    "newly_introduced_phone_number", "newly_introduced_currency_amount",
    "original_named_entities_or_brand_tokens", "rewrite_named_entities_or_brand_tokens",
    "possible_entity_loss", "possible_entity_addition", "duplicate_rewrite",
    "all_safety_checks_passed", "risk_level", "risk_explanation",
    "human_review_decision", "human_review_notes",
]


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def normalize_text(value: object) -> str:
    return " ".join(WORD_RE.findall(str(value).casefold()))


def word_tokens(value: object) -> set[str]:
    return set(WORD_RE.findall(str(value).casefold()))


def token_overlap(original: object, rewrite: object) -> float:
    left, right = word_tokens(original), word_tokens(rewrite)
    union = left | right
    return 1.0 if not union else len(left & right) / len(union)


def canonical_urlish(value: str) -> str:
    token = value.casefold().replace("hxxps://", "").replace("hxxp://", "")
    token = token.replace("https://", "").replace("http://", "")
    return token.replace("[.]", ".").replace("(dot)", ".").rstrip(".,;:!?")


def matches(pattern: re.Pattern[str], value: object, *, canonical: bool = False) -> Counter[str]:
    found = pattern.findall(str(value))
    values = [canonical_urlish(item) if canonical else item.casefold().strip(".,;:!?") for item in found]
    return Counter(values)


def plausible_urlish_matches(value: object) -> Counter[str]:
    """Reject sentence-boundary false positives such as ``account. Visit``."""
    found = Counter()
    for raw in URLISH_RE.findall(str(value)):
        canonical = canonical_urlish(raw)
        host = canonical.split("/", 1)[0]
        suffix = host.rsplit(".", 1)[-1] if "." in host else ""
        explicit_scheme = bool(re.match(r"(?i)^(?:https?://|hxxps?://)", raw))
        if explicit_scheme or "/" in canonical or len(suffix) == 2 or suffix in COMMON_TLDS:
            found[canonical] += 1
    return found


def plausible_domain_matches(value: object) -> Counter[str]:
    found = Counter()
    for raw in DOMAIN_RE.findall(str(value)):
        canonical = canonical_urlish(raw)
        suffix = canonical.rsplit(".", 1)[-1]
        if len(suffix) == 2 or suffix in COMMON_TLDS:
            found[canonical] += 1
    return found


def entity_or_brand_tokens(value: object) -> list[str]:
    """Return explainable candidates: placeholders, acronyms, and capitalized tokens.

    This heuristic deliberately does not claim named-entity recognition. It only
    highlights token changes for a human reviewer.
    """
    text = str(value)
    candidates: set[str] = set(re.findall(r"\[[A-Za-z][A-Za-z0-9_ -]*\]", text))
    for match in re.finditer(r"\b[A-Za-z][A-Za-z0-9&.-]*\b", text):
        token = match.group(0)
        folded = token.casefold().strip(".-")
        if folded in ENTITY_STOPWORDS or len(folded) < 2:
            continue
        if token.isupper() or (token[0].isupper() and match.start() != 0):
            candidates.add(token)
    return sorted(candidates, key=str.casefold)


def load_pairs(source_path: Path) -> pd.DataFrame:
    source = pd.read_csv(source_path, keep_default_na=False)
    required = {"pair_id", "condition", "text", "generation_status"}
    missing = sorted(required - set(source.columns))
    if missing:
        raise ValueError(f"Source CSV is missing columns: {missing}")
    originals = source[source["condition"].eq(ORIGINAL)].copy()
    rewrites = source[source["condition"].eq(REWRITE) & source["generation_status"].eq("completed")].copy()
    if rewrites.empty:
        raise ValueError("No completed T1_llm_neutral_rewrite rows found")
    for name, frame in (("original", originals), ("completed rewrite", rewrites)):
        if frame["pair_id"].astype(str).str.strip().eq("").any() or frame["pair_id"].duplicated().any():
            raise ValueError(f"Every {name} pair_id must exist exactly once")
    unknown = sorted(set(rewrites["pair_id"]) - set(originals["pair_id"]))
    if unknown:
        raise ValueError(f"Completed rewrites have no matching original: {unknown}")
    merged = rewrites[["pair_id", "text"]].rename(columns={"text": "rewrite_text"}).merge(
        originals[["pair_id", "text"]].rename(columns={"text": "original_text"}),
        on="pair_id", how="left", validate="one_to_one",
    )
    return merged.sort_values("pair_id", kind="stable").reset_index(drop=True)


def triage_rows(pairs: pd.DataFrame) -> pd.DataFrame:
    normalized_rewrites = pairs["rewrite_text"].map(normalize_text)
    duplicate_counts = normalized_rewrites.value_counts()
    records = []
    for row in pairs.itertuples(index=False):
        original, rewrite = str(row.original_text), str(row.rewrite_text)
        original_norm, rewrite_norm = normalize_text(original), normalize_text(rewrite)
        original_urls = plausible_urlish_matches(original)
        rewrite_urls = plausible_urlish_matches(rewrite)
        original_url_placeholders = matches(URL_PLACEHOLDER_RE, original)
        rewrite_url_placeholders = matches(URL_PLACEHOLDER_RE, rewrite)
        original_live = matches(LIVE_URL_RE, original, canonical=True)
        rewrite_live = matches(LIVE_URL_RE, rewrite, canonical=True)
        original_domains = plausible_domain_matches(original)
        rewrite_domains = plausible_domain_matches(rewrite)
        original_entities = entity_or_brand_tokens(original)
        rewrite_entities = entity_or_brand_tokens(rewrite)
        original_entity_keys = {value.casefold() for value in original_entities}
        rewrite_entity_keys = {value.casefold() for value in rewrite_entities}

        exact = original == rewrite
        normalized_equal = original_norm == rewrite_norm
        ratio = len(rewrite) / max(1, len(original))
        overlap = token_overlap(original, rewrite)
        defanged_preserved = not bool((original_urls - rewrite_urls) or (original_url_placeholders - rewrite_url_placeholders))
        new_url = bool((rewrite_urls - original_urls) or (rewrite_live - original_live))
        new_domain = bool(rewrite_domains - original_domains)
        new_email = bool(matches(EMAIL_RE, rewrite) - matches(EMAIL_RE, original))
        new_phone = bool(matches(PHONE_RE, rewrite) - matches(PHONE_RE, original))
        new_amount = bool(matches(AMOUNT_RE, rewrite) - matches(AMOUNT_RE, original))
        entity_loss = bool(original_entity_keys - rewrite_entity_keys)
        entity_addition = bool(rewrite_entity_keys - original_entity_keys)
        duplicate = bool(rewrite_norm and duplicate_counts.get(rewrite_norm, 0) > 1)
        operational = new_url or new_domain or new_email or new_phone or new_amount
        high_reasons = []
        if operational: high_reasons.append("new operational detail")
        if not defanged_preserved: high_reasons.append("original defanged URL/placeholder not preserved")
        if exact: high_reasons.append("rewrite exactly equals original")
        elif normalized_equal: high_reasons.append("rewrite equals original after normalization")
        if duplicate: high_reasons.append("rewrite duplicates another completed rewrite")
        medium_reasons = []
        if entity_loss: medium_reasons.append("possible entity/brand token loss")
        if entity_addition: medium_reasons.append("possible entity/brand token addition")
        if not LENGTH_RATIO_MIN <= ratio <= LENGTH_RATIO_MAX: medium_reasons.append("extreme length change")
        if overlap < TOKEN_OVERLAP_MIN: medium_reasons.append("low lexical overlap")
        risk = "high" if high_reasons else "medium" if medium_reasons else "low"
        reasons = high_reasons if high_reasons else medium_reasons
        records.append({
            "pair_id": str(row.pair_id), "original_text": original, "rewrite_text": rewrite,
            "exact_match_with_original": exact, "normalized_text_match": normalized_equal,
            "original_length": len(original), "rewrite_length": len(rewrite),
            "length_ratio": round(ratio, 4), "token_overlap_ratio": round(overlap, 4),
            "defanged_url_preserved": defanged_preserved, "newly_introduced_url": new_url,
            "newly_introduced_domain": new_domain, "newly_introduced_email": new_email,
            "newly_introduced_phone_number": new_phone,
            "newly_introduced_currency_amount": new_amount,
            "original_named_entities_or_brand_tokens": json.dumps(original_entities, ensure_ascii=False),
            "rewrite_named_entities_or_brand_tokens": json.dumps(rewrite_entities, ensure_ascii=False),
            "possible_entity_loss": entity_loss, "possible_entity_addition": entity_addition,
            "duplicate_rewrite": duplicate,
            "all_safety_checks_passed": not (operational or not defanged_preserved or exact or normalized_equal or duplicate),
            "risk_level": risk, "risk_explanation": "; ".join(reasons) if reasons else "no deterministic risk flag",
            "human_review_decision": "", "human_review_notes": "",
        })
    output = pd.DataFrame(records, columns=QUEUE_COLUMNS)
    order = pd.Categorical(output["risk_level"], categories=["high", "medium", "low"], ordered=True)
    return output.assign(_risk_order=order).sort_values(["_risk_order", "pair_id"], kind="stable").drop(columns="_risk_order").reset_index(drop=True)


def atomic_write_csv(frame: pd.DataFrame, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, name = tempfile.mkstemp(prefix=f".{path.stem}_", suffix=".tmp", dir=path.parent)
    os.close(descriptor); temporary = Path(name)
    try:
        frame.to_csv(temporary, index=False, lineterminator="\n")
        os.replace(temporary, path)
    finally:
        if temporary.exists(): temporary.unlink()


def atomic_write_text(text: str, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, name = tempfile.mkstemp(prefix=f".{path.stem}_", suffix=".tmp", dir=path.parent)
    os.close(descriptor); temporary = Path(name)
    try:
        temporary.write_text(text, encoding="utf-8")
        os.replace(temporary, path)
    finally:
        if temporary.exists(): temporary.unlink()


def build_triage(source_path: Path = DEFAULT_SOURCE, queue_path: Path = DEFAULT_QUEUE,
                 json_path: Path = DEFAULT_JSON, markdown_path: Path = DEFAULT_MARKDOWN) -> dict:
    before = file_sha256(source_path)
    queue = triage_rows(load_pairs(source_path))
    counts = queue["risk_level"].value_counts().to_dict()
    summary = {
        "scope": "offline deterministic triage; not human review",
        "source": source_path.as_posix(), "source_sha256": before,
        "eligible_completed_rewrites": len(queue),
        "risk_counts": {level: int(counts.get(level, 0)) for level in ("high", "medium", "low")},
        "human_decisions_prefilled": 0,
        "thresholds": {"length_ratio_min": LENGTH_RATIO_MIN, "length_ratio_max": LENGTH_RATIO_MAX, "token_overlap_min": TOKEN_OVERLAP_MIN},
        "limitations": [
            "Triage cannot establish semantic preservation, requested-action preservation, label preservation, or naturalness.",
            "Entity/brand tokens are explainable surface heuristics, not named-entity recognition.",
            "No row is auto-approved or auto-rejected; a human decision is required.",
        ],
    }
    atomic_write_csv(queue, queue_path)
    atomic_write_text(json.dumps(summary, indent=2, ensure_ascii=False) + "\n", json_path)
    markdown = f"""# Benchmark v1 rewrite review triage summary

> Offline deterministic triage only. This is not human review and cannot establish semantic preservation or naturalness.

- Eligible completed rewrites: **{len(queue)}**
- High risk: **{summary['risk_counts']['high']}**
- Medium risk: **{summary['risk_counts']['medium']}**
- Low risk: **{summary['risk_counts']['low']}**
- Human decisions prefilled: **0**

High risk means at least one new operational detail, missing defanged URL/placeholder, exact or normalized equality, or a duplicate rewrite. Medium risk means no high-risk flag but possible entity-token loss/addition, an extreme length ratio outside `{LENGTH_RATIO_MIN}–{LENGTH_RATIO_MAX}`, or token overlap below `{TOKEN_OVERLAP_MIN}`. Low risk means no deterministic flag.

The queue contains no detector predictions or probabilities. Reviewers must independently assess semantic intent, requested action, label preservation, and naturalness. Triage never approves or rejects a row.
"""
    atomic_write_text(markdown, markdown_path)
    if file_sha256(source_path) != before:
        raise RuntimeError("Source CSV changed while building triage")
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, default=DEFAULT_SOURCE)
    parser.add_argument("--queue", type=Path, default=DEFAULT_QUEUE)
    parser.add_argument("--summary-json", type=Path, default=DEFAULT_JSON)
    parser.add_argument("--summary-md", type=Path, default=DEFAULT_MARKDOWN)
    args = parser.parse_args()
    summary = build_triage(args.source, args.queue, args.summary_json, args.summary_md)
    print(json.dumps(summary["risk_counts"], sort_keys=True))
    print(f"Queue: {args.queue}")


if __name__ == "__main__":
    main()
