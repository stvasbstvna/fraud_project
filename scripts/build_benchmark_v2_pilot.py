"""Build deterministic, researcher-authored, non-operational Benchmark v2 pilot files."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
from pathlib import Path
from typing import Any


DEFAULT_OUTPUT = Path("data/benchmark_v2/pilot")
PILOT_STATUS = "researcher_authored_nonoperational_dry_run"
WARNING = "PILOT-ONLY: not eligible for final detector evaluation or detector-weakness claims."
SOURCE_ID = "BV2-PILOT-SRC-0001"
STYLE_SLOTS = ("brief", "plain", "routine", "conversational")
CONDITIONS = ("C0", "C1", "C2", "C3")
PHISHING_PLACEHOLDERS = (
    "[DEFANGED-ALERT-LINK]",
    "[DEFANGED-NOTICE-LINK]",
    "[DEFANGED-UPDATE-LINK]",
)

FAMILIES: tuple[dict[str, Any], ...] = (
    {"name": "unusual_transaction", "phishing_claim": "A generic transaction alert is available", "legitimate_claim": "A generic transaction summary is available", "placeholder": "[DEFANGED-ALERT-LINK]", "action": "review_transaction_notice", "tactics": ["institutional_notice"]},
    {"name": "card_restriction", "phishing_claim": "A generic card-status notice is available", "legitimate_claim": "A generic card-status summary is available", "placeholder": "[DEFANGED-NOTICE-LINK]", "action": "review_card_notice", "tactics": ["routine_notification"]},
    {"name": "payment_confirmation", "phishing_claim": "A generic payment notice is available", "legitimate_claim": "A generic payment summary is available", "placeholder": "[DEFANGED-NOTICE-LINK]", "action": "review_payment_notice", "tactics": ["routine_notification"]},
    {"name": "account_profile_update", "phishing_claim": "A generic profile-update notice is available", "legitimate_claim": "A generic profile-update summary is available", "placeholder": "[DEFANGED-UPDATE-LINK]", "action": "review_profile_notice", "tactics": ["helpfulness"]},
    {"name": "statement_availability", "phishing_claim": "A generic statement notice is available", "legitimate_claim": "A generic statement summary is available", "placeholder": "[DEFANGED-NOTICE-LINK]", "action": "review_statement_notice", "tactics": ["routine_notification"]},
    {"name": "card_delivery", "phishing_claim": "A generic card-delivery notice is available", "legitimate_claim": "A generic card-delivery summary is available", "placeholder": "[DEFANGED-UPDATE-LINK]", "action": "review_delivery_notice", "tactics": ["helpfulness"]},
)

REVIEW_FIELDS = (
    "semantic_intent_preserved",
    "requested_action_preserved",
    "label_preserved",
    "entities_placeholders_preserved",
    "no_operational_detail_added",
    "rewrite_is_different",
    "condition_fit",
    "action_explicitness_1_to_5",
    "decision",
    "rejection_reason",
    "review_notes",
)


def _json_line(record: dict[str, Any]) -> str:
    return json.dumps(record, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def _write_jsonl(path: Path, records: list[dict[str, Any]]) -> None:
    path.write_text("".join(_json_line(record) + "\n" for record in records), encoding="utf-8", newline="\n")


def _scenario_id(population: str, number: int) -> str:
    code = "P" if population == "phishing" else "L"
    return f"BV2-PILOT-{code}-{number:03d}"


def build_frames() -> list[dict[str, Any]]:
    frames: list[dict[str, Any]] = []
    for population, binary_label in (("phishing", 1), ("legitimate", 0)):
        number = 0
        for family in FAMILIES:
            for style_slot in STYLE_SLOTS:
                number += 1
                placeholder = family["placeholder"] if population == "phishing" else None
                claim = family["phishing_claim"] if population == "phishing" else family["legitimate_claim"]
                frames.append({
                    "scenario_id": _scenario_id(population, number),
                    "population": population,
                    "binary_label": binary_label,
                    "scenario_family": family["name"],
                    "style_slot": style_slot,
                    "claim": claim,
                    "requested_action_category": family["action"],
                    "tactic_tags": family["tactics"],
                    "entity_placeholders": [placeholder] if placeholder else [],
                    "url_state": "defanged_placeholder" if placeholder else "official_app_only",
                    "url_placeholder": placeholder,
                    "prohibited_changes": ["urgency", "new_consequence", "credential_request", "payment_instruction", "new_fact", "live_destination", "real_contact_detail", "detector_feedback"],
                    "source_manifest_id": SOURCE_ID,
                    "pilot_status": PILOT_STATUS,
                    "final_benchmark_eligible": False,
                    "notes": "Researcher-authored abstract frame with no real entity, person, account, destination, or operational detail.",
                })
    return frames


def _texts(frame: dict[str, Any]) -> dict[str, str]:
    claim = str(frame["claim"])
    style = str(frame["style_slot"])
    if frame["population"] == "phishing":
        destination = str(frame["url_placeholder"])
        c0_tail = f"notice at {destination}"
        c1_tail = f"The notice can be reviewed at {destination}."
        c2_tail = f"Please open {destination} and review the notice."
        c3_tail = f"Details are available at {destination}."
    else:
        c0_tail = "notice in official app"
        c1_tail = "The notice can be reviewed in the official app."
        c2_tail = "Please open the official app and review the notice."
        c3_tail = "Details are available in the official app."

    c0_prefix = {"brief": "brief", "plain": "plain notice", "routine": "routine note", "conversational": "quick note"}[style]
    c1_prefix = {"brief": "Brief notice:", "plain": "Plain notice:", "routine": "Routine note:", "conversational": "A quick note:"}[style]
    c2_prefix = {"brief": "Short update:", "plain": "For your information:", "routine": "Here is a routine update:", "conversational": "Just a quick update:"}[style]
    c0 = f"{c0_prefix}: {claim.lower()}; {c0_tail}."
    c1 = f"{c1_prefix} {claim}. {c1_tail}"
    c2 = f"{c2_prefix} {claim}. {c2_tail}"
    c3 = f"{c2_prefix} {claim}. {c3_tail}"
    return {"C0": c0, "C1": c1, "C2": c2, "C3": c3}


def build_variants(frames: list[dict[str, Any]]) -> list[dict[str, Any]]:
    variants: list[dict[str, Any]] = []
    for frame in frames:
        texts = _texts(frame)
        for condition in CONDITIONS:
            variants.append({
                "variant_id": f"{frame['scenario_id']}-{condition}",
                "scenario_id": frame["scenario_id"],
                "population": frame["population"],
                "binary_label": frame["binary_label"],
                "scenario_family": frame["scenario_family"],
                "style_slot": frame["style_slot"],
                "condition": condition,
                "parent_condition": None if condition == "C0" else "C2" if condition == "C3" else "C0",
                "text": texts[condition],
                "claim": frame["claim"],
                "requested_action_category": frame["requested_action_category"],
                "entity_placeholders": frame["entity_placeholders"],
                "creation_method": PILOT_STATUS,
                "generator_metadata": None,
                "prompt_id": None,
                "human_review_status": "pending",
                "final_benchmark_eligible": False,
                "pilot_status": PILOT_STATUS,
                "warning": WARNING,
            })
    texts = [record["text"] for record in variants]
    if len(texts) != len(set(texts)):
        raise RuntimeError("Pilot variant texts must be globally unique")
    return variants


def build_jobs(variants: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [{
        "job_id": f"JOB-{record['variant_id']}",
        "scenario_id": record["scenario_id"],
        "target_condition": record["condition"],
        "status": "not_run",
        "detector_access": "prohibited",
        "generator_block_id": None,
        "prompt_id": None,
        "final_benchmark_eligible": False,
        "warning": WARNING,
    } for record in variants if record["condition"] in {"C1", "C2", "C3"}]


def source_manifest() -> list[dict[str, Any]]:
    return [{
        "source_manifest_id": SOURCE_ID,
        "source_type": "researcher_authored_nonoperational_dry_run",
        "third_party_text_copied": False,
        "personal_data_present": False,
        "live_url_or_operational_detail_present": False,
        "final_benchmark_eligible": False,
        "permitted_use": "workflow_and_rubric_calibration_only",
        "statement": "No third-party text, personal data, live URL, or operational detail is included.",
    }]


def pilot_readme() -> str:
    return """# Benchmark v2 non-operational pilot materials

> **PILOT-ONLY — NOT ELIGIBLE FOR FINAL DETECTOR EVALUATION.**

This directory contains deterministic, researcher-authored, non-operational dry-run material. It is **not LLM-generated**, is **not a licensed real-world final benchmark**, and must not be used to claim that a detector is weaker.

Its only purpose is to test schema handling, validation, review workflow, and C0/C1/C2/C3 condition logic. It contains generic claims, generic “official app” directions for legitimate records, and visibly defanged placeholders for phishing-labelled records. It contains no real brand, person, phone number, credential, payment route, account number, live URL, or operational destination.

The pilot follows the frozen direction choice: C2 uses a direct review/open request and C3 preserves the same action while expressing it less explicitly. C3 must not add or replace an action.

Future final data must use authorized anchors, frozen prompts, a documented versioned generator pool, human approval, and detector-blinded generation. These pilot records have `final_benchmark_eligible=false` and must remain isolated from final evaluation inputs.

Rebuild deterministically from the repository root:

```powershell
uv run python .\\scripts\\build_benchmark_v2_pilot.py
```

Generated files contain 48 frames (24 phishing, 24 legitimate), 192 unique condition variants, 144 explicitly unrun jobs, an empty review queue, a source statement, and checksums. `SHA256SUMS.json` hashes every generated artifact except itself.
"""


def _write_review_csv(path: Path, variants: list[dict[str, Any]]) -> None:
    columns = ["variant_id", "scenario_id", "population", "condition", "warning", *REVIEW_FIELDS]
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns, lineterminator="\n")
        writer.writeheader()
        for record in variants:
            row = {column: "" for column in columns}
            row.update({key: record[key] for key in ("variant_id", "scenario_id", "population", "condition", "warning")})
            writer.writerow(row)


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def build_pilot(output_dir: Path = DEFAULT_OUTPUT) -> dict[str, int]:
    output_dir.mkdir(parents=True, exist_ok=True)
    frames = build_frames()
    variants = build_variants(frames)
    jobs = build_jobs(variants)
    _write_jsonl(output_dir / "semantic_frames_pilot.jsonl", frames)
    _write_jsonl(output_dir / "variants_dry_run_pilot.jsonl", variants)
    _write_jsonl(output_dir / "generation_jobs_not_run.jsonl", jobs)
    _write_review_csv(output_dir / "human_review_queue.csv", variants)
    _write_jsonl(output_dir / "source_manifest_pilot.jsonl", source_manifest())
    (output_dir / "README.md").write_text(pilot_readme(), encoding="utf-8", newline="\n")
    hashed_names = ["semantic_frames_pilot.jsonl", "variants_dry_run_pilot.jsonl", "generation_jobs_not_run.jsonl", "human_review_queue.csv", "source_manifest_pilot.jsonl", "README.md"]
    checksums = {name: _sha256(output_dir / name) for name in hashed_names}
    (output_dir / "SHA256SUMS.json").write_text(json.dumps(checksums, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")
    return {"frames": len(frames), "variants": len(variants), "jobs": len(jobs), "review_rows": len(variants)}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    counts = build_pilot(args.output_dir)
    print(f"Built Benchmark v2 pilot: {counts}")
    print(f"Output: {args.output_dir}")
    print(WARNING)


if __name__ == "__main__":
    main()
