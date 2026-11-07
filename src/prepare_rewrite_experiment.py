"""Freeze the banking test and create a paired original/LLM-rewrite template."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pandas as pd


INPUT = Path("data/final/banking_original_test.csv")
TRAIN_INPUT = Path("data/final/train_sms.csv")
OUT_DIR = Path("data/rewrite_experiment")
RESULT_DIR = Path("results/rewrite_experiment")
MODEL_DIR = Path("models/final")
FROZEN_INPUT = OUT_DIR / "original_banking_test_frozen.csv"
TEMPLATE = OUT_DIR / "rewrite_pairs.csv"
HASHES = RESULT_DIR / "model_hashes.csv"
METADATA = RESULT_DIR / "experiment_design.json"
PROMPT_ID = "neutral_rewrite_v1"
MODEL_SNAPSHOT = "gpt-5.4-mini-2026-03-17"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def build_pairs(frame: pd.DataFrame) -> pd.DataFrame:
    required = {
        "id", "text", "binary_label", "class_label", "source_dataset",
        "intent_type", "requested_action", "split",
    }
    missing = sorted(required.difference(frame.columns))
    if missing:
        raise ValueError(f"Banking test is missing columns: {missing}")
    if len(frame) != 156:
        raise ValueError(f"Expected 156 frozen banking rows, found {len(frame)}")
    if not frame["id"].is_unique:
        raise ValueError("Banking test IDs are not unique")
    if not frame["split"].eq("banking_test").all():
        raise ValueError("Frozen input contains rows outside banking_test")
    class_counts = frame["binary_label"].value_counts().to_dict()
    if class_counts != {1: 146, 0: 10}:
        raise ValueError(f"Expected 146 phishing and 10 non-phishing rows, found {class_counts}")

    rows: list[dict[str, object]] = []
    for index, row in frame.sort_values("id").reset_index(drop=True).iterrows():
        pair_id = f"BRW-{index + 1:04d}"
        common = {
            "pair_id": pair_id,
            "original_id": row["id"],
            "source_dataset": row["source_dataset"],
            "true_label": row["class_label"],
            "binary_label": int(row["binary_label"]),
            "intent_type": row.get("intent_type", ""),
            "requested_action": row.get("requested_action", ""),
            "original_text": row["text"],
        }
        rows.append({
            **common,
            "condition": "T0_original",
            "text": row["text"],
            "prompt_id": "not_applicable",
            "generator_model": "not_applicable",
            "response_id": "",
            "generated_at_utc": "",
            "generation_status": "original",
            "generation_attempts": 0,
            "rejection_reason": "",
            "safety_check_passed": True,
            "human_review_status": "not_applicable",
            "semantic_intent_preserved": "not_applicable",
            "requested_action_preserved": "not_applicable",
            "label_preserved": "not_applicable",
            "review_notes": "",
        })
        rows.append({
            **common,
            "condition": "T1_llm_neutral_rewrite",
            "text": "",
            "prompt_id": PROMPT_ID,
            "generator_model": MODEL_SNAPSHOT,
            "response_id": "",
            "generated_at_utc": "",
            "generation_status": "pending",
            "generation_attempts": 0,
            "rejection_reason": "",
            "safety_check_passed": False,
            "human_review_status": "pending",
            "semantic_intent_preserved": "pending",
            "requested_action_preserved": "pending",
            "label_preserved": "pending",
            "review_notes": "",
        })
    return pd.DataFrame(rows)


def validate_no_training_overlap(frozen: pd.DataFrame, train: pd.DataFrame) -> None:
    if "id" not in train.columns:
        raise ValueError("Training data is missing id")
    overlap = sorted(set(frozen["id"].astype(str)) & set(train["id"].astype(str)))
    if overlap:
        raise ValueError(f"Frozen banking-test rows appear in training: {overlap[:5]}")


def load_or_create_frozen(source: pd.DataFrame) -> pd.DataFrame:
    if FROZEN_INPUT.exists():
        frozen = pd.read_csv(FROZEN_INPUT)
        if sha256(INPUT) != sha256(FROZEN_INPUT):
            raise ValueError("Existing frozen banking test differs from data/final/banking_original_test.csv")
        return frozen
    source.to_csv(FROZEN_INPUT, index=False, lineterminator="\n")
    return pd.read_csv(FROZEN_INPUT)


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    source = pd.read_csv(INPUT)
    frame = load_or_create_frozen(source)
    validate_no_training_overlap(frame, pd.read_csv(TRAIN_INPUT))
    pairs = build_pairs(frame)
    if TEMPLATE.exists():
        existing = pd.read_csv(TEMPLATE, keep_default_na=False)
        completed = existing[
            existing["condition"].eq("T1_llm_neutral_rewrite")
            & existing["text"].astype(str).str.strip().ne("")
        ]
        if not completed.empty:
            if set(existing["pair_id"]) != set(pairs["pair_id"]):
                raise ValueError("Existing rewrite pairs do not match the frozen experiment")
            pairs = existing
        else:
            pairs.to_csv(TEMPLATE, index=False, lineterminator="\n")
    else:
        pairs.to_csv(TEMPLATE, index=False, lineterminator="\n")

    model_rows = []
    for path in sorted(MODEL_DIR.glob("*.joblib")):
        model_rows.append({"model_file": path.as_posix(), "sha256": sha256(path)})
    if len(model_rows) != 2:
        raise ValueError(f"Expected two frozen model files, found {len(model_rows)}")
    pd.DataFrame(model_rows).to_csv(HASHES, index=False, lineterminator="\n")

    counts = pairs.groupby(["condition", "true_label"]).size().rename("rows").reset_index()
    metadata = {
        "primary_generator_model": MODEL_SNAPSHOT,
        "prompt_id": PROMPT_ID,
        "frozen_input": str(FROZEN_INPUT),
        "pairs": 156,
        "rows": 312,
        "phishing_pairs": int((frame["binary_label"] == 1).sum()),
        "non_phishing_pairs": int((frame["binary_label"] == 0).sum()),
        "detector_feedback_used": False,
        "detectors_retrained": False,
    }
    METADATA.write_text(json.dumps(metadata, indent=2), encoding="utf-8")
    print(counts.to_string(index=False))
    print(f"\nSaved: {TEMPLATE}")
    print(f"Saved model hashes: {HASHES}")


if __name__ == "__main__":
    main()
