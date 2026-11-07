"""Local human-in-the-loop review app for completed banking-smishing rewrites.

The app never writes to ``rewrite_pairs.csv``. Human decisions are persisted in
an independent CSV after every explicit action.
"""

from __future__ import annotations

import hashlib
import os
import re
import tempfile
from collections import Counter
from datetime import datetime, timezone
from difflib import SequenceMatcher
from pathlib import Path

import pandas as pd


SOURCE_PATH = Path("data/rewrite_experiment/rewrite_pairs.csv")
DECISIONS_PATH = Path("data/rewrite_experiment/human_review/review_decisions.csv")
CONDITION = "T1_llm_neutral_rewrite"
REVIEW_SEED = 20260827

CRITERION_COLUMNS = [
    "human_semantic_intent_preserved",
    "human_requested_action_preserved",
    "human_label_preserved",
    "human_entities_preserved",
    "human_no_operational_detail_added",
    "human_rewrite_is_different",
    "human_condition_fit",
]
REJECTION_REASONS = [
    "semantic_intent_changed",
    "requested_action_changed",
    "label_changed",
    "entity_or_fact_changed",
    "operational_detail_added",
    "live_or_unsafe_destination",
    "rewrite_equals_original",
    "condition_violation",
    "corrupted_or_unreadable",
    "other",
]
DECISION_COLUMNS = [
    "review_order",
    "pair_id",
    "original_id",
    "original_text_sha256",
    "rewrite_text_sha256",
    "risk_level",
    *CRITERION_COLUMNS,
    "human_review_status",
    "rejection_reason",
    "review_notes",
    "reviewer_id",
    "reviewed_at_utc",
]

PLACEHOLDER_RE = re.compile(r"\[[A-Za-z][A-Za-z0-9_ -]*\]")
LIVE_URL_RE = re.compile(r"(?i)\bhttps?://[^\s<>]+")
NUMBER_RE = re.compile(r"(?<![A-Za-z])\d+(?:[.,]\d+)*(?![A-Za-z])")
AMOUNT_RE = re.compile(
    r"(?i)(?:[$£€]\s*\d+(?:[.,]\d+)*|\d+(?:[.,]\d+)*\s*(?:usd|gbp|eur|dollars?|pounds?|euros?))"
)
PHONE_RE = re.compile(r"(?<!\w)(?:\+?\d[\d ()-]{5,}\d)(?!\w)")
EMAIL_RE = re.compile(r"(?i)\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b")
URLISH_RE = re.compile(
    r"(?i)\b(?:https?://|hxxps?://)?(?:[a-z0-9-]+(?:\[\.\]|\(dot\)|\.)+)+[a-z]{2,}(?:[/\\][^\s]*)?"
)
WORD_RE = re.compile(r"\w+|[^\w\s]", re.UNICODE)


def text_sha256(value: object) -> str:
    return hashlib.sha256(str(value).encode("utf-8")).hexdigest()


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_completed_rewrites(source_path: Path = SOURCE_PATH) -> pd.DataFrame:
    source = pd.read_csv(source_path, keep_default_na=False)
    required = {
        "pair_id", "original_id", "true_label", "intent_type",
        "requested_action", "original_text", "text", "condition",
        "generation_status",
    }
    missing = sorted(required.difference(source.columns))
    if missing:
        raise ValueError(f"Source CSV is missing columns: {missing}")
    eligible = source[
        source["condition"].eq(CONDITION)
        & source["generation_status"].eq("completed")
    ].copy()
    if eligible["pair_id"].astype(str).str.strip().eq("").any():
        raise ValueError("Completed rows contain an empty pair_id")
    if eligible["pair_id"].duplicated().any():
        raise ValueError("Completed rows contain duplicate pair IDs")
    return eligible.reset_index(drop=True)


def deterministic_review_order(rows: pd.DataFrame, seed: int = REVIEW_SEED) -> pd.DataFrame:
    ordered = rows.sample(frac=1, random_state=seed).reset_index(drop=True).copy()
    ordered["review_order"] = range(1, len(ordered) + 1)
    return ordered


def _normalized(value: object) -> str:
    return " ".join(re.findall(r"\w+", str(value).casefold(), flags=re.UNICODE))


def _tokens(pattern: re.Pattern[str], value: object) -> Counter[str]:
    return Counter(match.casefold().strip(".,;:!?") for match in pattern.findall(str(value)))


def _canonical_urlish(token: str) -> str:
    value = token.casefold().replace("hxxps://", "").replace("hxxp://", "")
    value = value.replace("https://", "").replace("http://", "")
    value = value.replace("[.]", ".").replace("(dot)", ".")
    return value.rstrip(".,;:!?")


def automated_checks(original: object, rewrite: object, requested_action: object = "") -> dict[str, object]:
    original_text, rewrite_text = str(original), str(rewrite)
    original_norm, rewrite_norm = _normalized(original_text), _normalized(rewrite_text)
    placeholders_original = _tokens(PLACEHOLDER_RE, original_text)
    placeholders_rewrite = _tokens(PLACEHOLDER_RE, rewrite_text)
    numbers_original, numbers_rewrite = _tokens(NUMBER_RE, original_text), _tokens(NUMBER_RE, rewrite_text)
    amounts_original, amounts_rewrite = _tokens(AMOUNT_RE, original_text), _tokens(AMOUNT_RE, rewrite_text)
    phones_original, phones_rewrite = _tokens(PHONE_RE, original_text), _tokens(PHONE_RE, rewrite_text)
    emails_original, emails_rewrite = _tokens(EMAIL_RE, original_text), _tokens(EMAIL_RE, rewrite_text)
    urls_original = Counter(_canonical_urlish(v) for v in URLISH_RE.findall(original_text))
    urls_rewrite = Counter(_canonical_urlish(v) for v in URLISH_RE.findall(rewrite_text))
    live_original, live_rewrite = _tokens(LIVE_URL_RE, original_text), _tokens(LIVE_URL_RE, rewrite_text)
    similarity = SequenceMatcher(None, original_norm, rewrite_norm).ratio() if original_norm or rewrite_norm else 1.0
    length_ratio = len(rewrite_text) / max(1, len(original_text))

    missing_placeholders = placeholders_original - placeholders_rewrite
    added_live_urls = live_rewrite - live_original
    changed_numbers = numbers_original != numbers_rewrite
    changed_amounts = amounts_original != amounts_rewrite
    changed_phones = phones_original != phones_rewrite
    changed_emails = emails_original != emails_rewrite
    missing_urls = urls_original - urls_rewrite
    added_urls = urls_rewrite - urls_original
    new_destination = bool(
        added_live_urls or added_urls or (emails_rewrite - emails_original)
        or (phones_rewrite - phones_original)
    )

    checks: dict[str, object] = {
        "rewrite_non_empty": bool(rewrite_text.strip()),
        "rewrite_differs": original_norm != rewrite_norm,
        "placeholders_preserved": not bool(missing_placeholders),
        "no_new_live_url": not bool(added_live_urls),
        "numeric_tokens_preserved": not changed_numbers,
        "currency_amounts_preserved": not changed_amounts,
        "phone_tokens_preserved": not changed_phones,
        "email_tokens_preserved": not changed_emails,
        "url_domain_path_preserved": not bool(missing_urls or added_urls),
        "length_ratio": round(length_ratio, 3),
        "normalized_similarity": round(similarity, 3),
        "requested_action_metadata_present": bool(str(requested_action).strip()),
        "no_new_destination_or_contact": not new_destination,
        "missing_placeholders": sorted(missing_placeholders.elements()),
        "added_live_urls": sorted(added_live_urls.elements()),
        "changed_numeric_tokens": changed_numbers,
        "changed_amounts": changed_amounts,
        "changed_phone_tokens": changed_phones,
        "changed_email_tokens": changed_emails,
        "missing_url_domain_path": sorted(missing_urls.elements()),
        "added_url_domain_path": sorted(added_urls.elements()),
    }

    red = (
        not checks["rewrite_non_empty"]
        or not checks["rewrite_differs"]
        or not checks["placeholders_preserved"]
        or not checks["no_new_live_url"]
        or not checks["currency_amounts_preserved"]
        or not checks["no_new_destination_or_contact"]
        or bool(missing_urls)
    )
    amber = (
        changed_numbers or changed_phones or changed_emails
        or similarity < 0.45 or not 0.55 <= length_ratio <= 1.8
        or bool(added_urls)
    )
    checks["risk_level"] = "red" if red else "amber" if amber else "green"
    return checks


def _new_decisions(rows: pd.DataFrame) -> pd.DataFrame:
    ordered = deterministic_review_order(rows)
    records = []
    for row in ordered.to_dict("records"):
        risk = automated_checks(row["original_text"], row["text"], row["requested_action"])["risk_level"]
        record = {
            "review_order": row["review_order"],
            "pair_id": str(row["pair_id"]),
            "original_id": str(row["original_id"]),
            "original_text_sha256": text_sha256(row["original_text"]),
            "rewrite_text_sha256": text_sha256(row["text"]),
            "risk_level": risk,
            **{column: "" for column in CRITERION_COLUMNS},
            "human_review_status": "",
            "rejection_reason": "",
            "review_notes": "",
            "reviewer_id": "",
            "reviewed_at_utc": "",
        }
        records.append(record)
    return pd.DataFrame(records, columns=DECISION_COLUMNS)


def atomic_write_csv(frame: pd.DataFrame, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temp_name = tempfile.mkstemp(prefix=f".{path.stem}_", suffix=".tmp", dir=path.parent)
    os.close(descriptor)
    temp_path = Path(temp_name)
    try:
        frame.to_csv(temp_path, index=False, lineterminator="\n")
        os.replace(temp_path, path)
    finally:
        if temp_path.exists():
            temp_path.unlink()


def load_or_create_decisions(
    rows: pd.DataFrame,
    decisions_path: Path = DECISIONS_PATH,
) -> pd.DataFrame:
    expected = _new_decisions(rows)
    if not decisions_path.exists():
        atomic_write_csv(expected, decisions_path)
        return expected
    existing = pd.read_csv(decisions_path, keep_default_na=False)
    missing = sorted(set(DECISION_COLUMNS).difference(existing.columns))
    if missing:
        raise ValueError(f"Decision file is missing columns: {missing}")
    if existing["pair_id"].duplicated().any():
        raise ValueError("Decision file contains duplicate pair IDs")
    expected_by_id = expected.set_index("pair_id")
    unknown = sorted(set(existing["pair_id"]) - set(expected_by_id.index))
    if unknown:
        raise ValueError(f"Decision file contains unknown/ineligible pair IDs: {unknown}")
    for row in existing.itertuples(index=False):
        expected_row = expected_by_id.loc[str(row.pair_id)]
        if str(row.original_text_sha256) != str(expected_row.original_text_sha256):
            raise ValueError(f"{row.pair_id}: original text hash no longer matches")
        if str(row.rewrite_text_sha256) != str(expected_row.rewrite_text_sha256):
            raise ValueError(f"{row.pair_id}: rewrite text hash no longer matches")
    missing_ids = [pair_id for pair_id in expected["pair_id"] if pair_id not in set(existing["pair_id"])]
    if missing_ids:
        additions = expected[expected["pair_id"].isin(missing_ids)].copy()
        additions["review_order"] = range(int(existing["review_order"].max()) + 1, int(existing["review_order"].max()) + 1 + len(additions))
        existing = pd.concat([existing[DECISION_COLUMNS], additions], ignore_index=True)
        atomic_write_csv(existing, decisions_path)
    return existing[DECISION_COLUMNS].sort_values("review_order").reset_index(drop=True)


def save_human_decision(
    decisions: pd.DataFrame,
    pair_id: str,
    action: str,
    *,
    reviewer_id: str,
    criteria: dict[str, str] | None = None,
    rejection_reason: str = "",
    review_notes: str = "",
    decisions_path: Path = DECISIONS_PATH,
) -> pd.DataFrame:
    if action not in {"approved", "rejected", "uncertain"}:
        raise ValueError(f"Unsupported explicit action: {action}")
    if not reviewer_id.strip():
        raise ValueError("reviewer_id is required")
    matches = decisions.index[decisions["pair_id"].astype(str).eq(str(pair_id))]
    if len(matches) != 1:
        raise ValueError("pair_id must exist exactly once in decisions")
    values = {column: str((criteria or {}).get(column, "")).strip().lower() for column in CRITERION_COLUMNS}
    if action == "approved":
        values = {column: "yes" for column in CRITERION_COLUMNS}
    elif action == "rejected":
        if rejection_reason not in REJECTION_REASONS:
            raise ValueError("Reject requires a valid rejection reason")
        if "no" not in values.values():
            raise ValueError("Reject requires at least one criterion set to no")
    else:
        if "no" in values.values():
            raise ValueError("A row with a no criterion must be rejected")
        if "uncertain" not in values.values():
            raise ValueError("Uncertain requires at least one uncertain criterion")
    if any(value not in {"yes", "no", "uncertain"} for value in values.values()):
        raise ValueError("Every criterion must be yes, no or uncertain")

    updated = decisions.copy()
    index = matches[0]
    for column, value in values.items():
        updated.at[index, column] = value
    updated.at[index, "human_review_status"] = action
    updated.at[index, "rejection_reason"] = rejection_reason if action == "rejected" else ""
    updated.at[index, "review_notes"] = review_notes.strip()
    updated.at[index, "reviewer_id"] = reviewer_id.strip()
    updated.at[index, "reviewed_at_utc"] = datetime.now(timezone.utc).isoformat()
    atomic_write_csv(updated[DECISION_COLUMNS], decisions_path)
    return updated[DECISION_COLUMNS]


def decision_summary(decisions: pd.DataFrame) -> dict[str, object]:
    status = decisions["human_review_status"].astype(str)
    risk = decisions["risk_level"].astype(str)
    reviewed = int(status.isin(["approved", "rejected", "uncertain"]).sum())
    return {
        "total_completed": len(decisions),
        "reviewed": reviewed,
        "remaining": len(decisions) - reviewed,
        "approved": int(status.eq("approved").sum()),
        "rejected": int(status.eq("rejected").sum()),
        "uncertain": int(status.eq("uncertain").sum()),
        "green": int(risk.eq("green").sum()),
        "amber": int(risk.eq("amber").sum()),
        "red": int(risk.eq("red").sum()),
        "rejection_reasons": decisions.loc[status.eq("rejected"), "rejection_reason"].value_counts().to_dict(),
    }


def _diff_markdown(original: str, rewrite: str) -> str:
    def escaped(token: str) -> str:
        return re.sub(r"([\\`*_{}\[\]()#+.!|<>~-])", r"\\\1", token)

    original_tokens, rewrite_tokens = WORD_RE.findall(original), WORD_RE.findall(rewrite)
    matcher = SequenceMatcher(None, original_tokens, rewrite_tokens)
    parts: list[str] = []
    for operation, i1, i2, j1, j2 in matcher.get_opcodes():
        if operation == "equal":
            parts.extend(escaped(token) for token in rewrite_tokens[j1:j2])
        elif operation in {"replace", "delete"}:
            removed = " ".join(escaped(token) for token in original_tokens[i1:i2])
            if removed:
                parts.append(f":red[~~{removed}~~]")
            if operation == "replace":
                added = " ".join(escaped(token) for token in rewrite_tokens[j1:j2])
                if added:
                    parts.append(f":green[**{added}**]")
        elif operation == "insert":
            added = " ".join(escaped(token) for token in rewrite_tokens[j1:j2])
            parts.append(f":green[**{added}**]")
    return " ".join(parts)


def _run_app() -> None:
    import streamlit as st

    st.set_page_config(page_title="Rewrite human review", page_icon=":material/fact_check:", layout="wide")
    st.title("Banking-smishing rewrite review")
    st.caption(f"Local deterministic review · seed {REVIEW_SEED} · no detector output and no external API")

    source_hash = file_sha256(SOURCE_PATH)
    rows = load_completed_rewrites(SOURCE_PATH)
    decisions = load_or_create_decisions(rows, DECISIONS_PATH)
    if file_sha256(SOURCE_PATH) != source_hash:
        st.error("Safety stop: the source CSV changed while the app was loading.")
        st.stop()
    source_by_pair = rows.set_index("pair_id", drop=False)
    summary = decision_summary(decisions)

    with st.sidebar:
        st.header("Review controls")
        reviewer_id = st.text_input("Reviewer ID", key="reviewer_id", placeholder="e.g. reviewer-01")
        filter_name = st.selectbox(
            "Filter",
            ["unreviewed", "green", "amber", "red", "approved", "rejected", "uncertain", "legitimate", "phishing"],
        )
        st.caption(f"Decisions are saved after every action to `{DECISIONS_PATH}`.")

    with st.container(horizontal=True):
        st.metric("Completed", summary["total_completed"], border=True)
        st.metric("Reviewed", summary["reviewed"], border=True)
        st.metric("Remaining", summary["remaining"], border=True)
        st.metric("Approved", summary["approved"], border=True)
        st.metric("Rejected", summary["rejected"], border=True)
        st.metric("Uncertain", summary["uncertain"], border=True)
    st.progress(summary["reviewed"] / max(1, summary["total_completed"]), text=f"{summary['reviewed']} of {summary['total_completed']} reviewed")

    view = decisions.copy()
    if filter_name == "unreviewed":
        view = view[view["human_review_status"].eq("")]
    elif filter_name in {"green", "amber", "red"}:
        view = view[view["risk_level"].eq(filter_name)]
    elif filter_name in {"approved", "rejected", "uncertain"}:
        view = view[view["human_review_status"].eq(filter_name)]
    else:
        labels = view["pair_id"].map(source_by_pair["true_label"])
        view = view[labels.eq(filter_name)]

    if view.empty:
        st.success("No rows match this filter.", icon=":material/check_circle:")
    else:
        pair_id = st.selectbox(
            "Review item",
            view["pair_id"].tolist(),
            format_func=lambda value: f"#{int(view.set_index('pair_id').loc[value, 'review_order'])} · {value}",
        )
        decision_row = decisions.set_index("pair_id").loc[pair_id]
        row = source_by_pair.loc[pair_id]
        checks = automated_checks(row["original_text"], row["text"], row["requested_action"])
        order = int(decision_row["review_order"])
        percent = 100 * order / len(decisions)
        st.subheader(f"{pair_id} · review order {order}/{len(decisions)} ({percent:.1f}%)")
        badge_color = {"green": "green", "amber": "orange", "red": "red"}[str(checks["risk_level"])]
        st.badge(f"Suggested risk: {checks['risk_level']}", color=badge_color)

        with st.container(horizontal=True):
            st.badge(str(row["true_label"]), color="blue")
            st.markdown(f"**Intent:** {row['intent_type']}")
            st.markdown(f"**Requested action:** {row['requested_action']}")

        original_col, rewrite_col = st.columns(2)
        with original_col:
            with st.container(border=True):
                st.subheader("Original")
                st.write(row["original_text"])
        with rewrite_col:
            with st.container(border=True):
                st.subheader("Rewrite")
                st.write(row["text"])
        with st.container(border=True):
            st.subheader("Word-level difference")
            st.markdown(_diff_markdown(str(row["original_text"]), str(row["text"])))

        with st.expander("Deterministic automated checks", expanded=checks["risk_level"] != "green", icon=":material/rule:"):
            for name, value in checks.items():
                if name == "risk_level":
                    continue
                if isinstance(value, bool):
                    st.write((":material/check_circle:" if value else ":material/error:") + f" {name}: {value}")
                else:
                    st.write(f"**{name}:** {value}")
            st.caption("These checks prioritize review attention. They never approve a row.")

        with st.form(f"review_{pair_id}", clear_on_submit=False):
            st.subheader("Human decision")
            criterion_values: dict[str, str] = {}
            for column in CRITERION_COLUMNS:
                current = str(decision_row[column])
                criterion_values[column] = st.selectbox(
                    column.replace("human_", "").replace("_", " "),
                    ["", "yes", "no", "uncertain"],
                    index=["", "yes", "no", "uncertain"].index(current) if current in {"", "yes", "no", "uncertain"} else 0,
                    key=f"{pair_id}_{column}",
                )
            rejection_reason = st.selectbox(
                "Rejection reason",
                [""] + REJECTION_REASONS,
                index=([""] + REJECTION_REASONS).index(str(decision_row["rejection_reason"])) if str(decision_row["rejection_reason"]) in REJECTION_REASONS else 0,
            )
            notes = st.text_area("Optional review notes", value=str(decision_row["review_notes"]))
            with st.container(horizontal=True):
                approve = st.form_submit_button("Approve", type="primary", icon=":material/check_circle:")
                reject = st.form_submit_button("Reject", icon=":material/cancel:")
                uncertain = st.form_submit_button("Uncertain", icon=":material/help:")
                skip = st.form_submit_button("Skip", icon=":material/skip_next:")

        action = "approved" if approve else "rejected" if reject else "uncertain" if uncertain else None
        if action:
            try:
                save_human_decision(
                    decisions, pair_id, action, reviewer_id=reviewer_id,
                    criteria=criterion_values, rejection_reason=rejection_reason,
                    review_notes=notes, decisions_path=DECISIONS_PATH,
                )
            except ValueError as error:
                st.error(str(error), icon=":material/error:")
            else:
                st.toast(f"{pair_id}: {action} saved", icon=":material/save:")
                st.rerun()
        elif skip:
            st.toast("Skipped without saving a decision", icon=":material/skip_next:")

    with st.expander("Final summary", icon=":material/summarize:"):
        with st.container(horizontal=True):
            st.metric("Green", summary["green"], border=True)
            st.metric("Amber", summary["amber"], border=True)
            st.metric("Red", summary["red"], border=True)
        if summary["rejection_reasons"]:
            st.dataframe(
                pd.DataFrame(summary["rejection_reasons"].items(), columns=["Rejection reason", "Count"]),
                hide_index=True,
            )
        else:
            st.caption("No rejection reasons recorded yet.")


if __name__ == "__main__":
    _run_app()
