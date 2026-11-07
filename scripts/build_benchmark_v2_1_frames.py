"""Build safe researcher-authored Benchmark v2.1 semantic frames and generation jobs.

This script does not call an LLM and does not run detectors. All destinations are
fixed defanged placeholders. The output is a frame specification plus generation
jobs for C1-C6; C0 is the researcher-authored anchor.
"""
from __future__ import annotations

import argparse
import hashlib
from pathlib import Path
import pandas as pd

BANKS = ["Northstar Bank", "Harbor Credit", "Pioneer Bank", "Summit Financial", "Cedar Bank", "MetroTrust"]
PHISHING_SCENARIOS = [
    ("account_access", "review an account-security notice", "security notice", "[DEFANGED-ALERT-LINK]"),
    ("card_activity", "review a card-activity notice", "card activity", "[DEFANGED-ALERT-LINK]"),
    ("transfer_review", "review a transfer notice", "transfer notice", "[DEFANGED-ALERT-LINK]"),
    ("identity_check", "review an identity-verification notice", "identity check", "[DEFANGED-ALERT-LINK]"),
    ("payment_review", "review a payment notice", "payment notice", "[DEFANGED-ALERT-LINK]"),
    ("deposit_review", "review a deposit notice", "deposit notice", "[DEFANGED-ALERT-LINK]"),
]
LEGIT_SCENARIOS = [
    ("deposit_confirmation", "read a deposit confirmation", "deposit confirmation", "[OFFICIAL-APP]"),
    ("card_confirmation", "read a card confirmation", "card confirmation", "[OFFICIAL-APP]"),
    ("transfer_confirmation", "read a transfer confirmation", "transfer confirmation", "[OFFICIAL-APP]"),
    ("security_education", "read a security reminder", "security reminder", "[OFFICIAL-APP]"),
    ("statement_ready", "view a statement notification", "statement notification", "[OFFICIAL-APP]"),
]

CONDITIONS = {
    "C0": "researcher-authored anchor",
    "C1": "minimal lexical variation",
    "C2": "direct requested action",
    "C3": "same requested action, softened/less direct expression",
    "C4": "natural-language normalization with semantic/action preservation",
    "C5": "strong lexical and syntactic paraphrase with semantic/action preservation",
    "C6": "combined high-distance semantic-preserving realization; softened directness permitted but action retained",
}


def _hash(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def phishing_anchor(bank: str, event: str, destination: str, i: int) -> str:
    amount = 40 + ((i * 37) % 1960)
    endings = [
        f"{bank}: We detected unusual {event}. Please open {destination} and review the notice.",
        f"{bank} alert: A ${amount}.00 {event} requires review. Please open {destination} and check the details.",
        f"{bank}: Your {event} notice is ready for review. Open {destination} to review the notice.",
    ]
    return endings[i % len(endings)]


def legitimate_anchor(bank: str, event: str, destination: str, i: int) -> str:
    amount = 10 + ((i * 19) % 490)
    endings = [
        f"{bank}: Your {event} is available in {destination}. No reply is required.",
        f"{bank}: A ${amount}.00 transaction update is available in {destination}. Open your official app if you want to review it.",
        f"{bank}: This is a routine {event}. You can review details through {destination}.",
    ]
    return endings[i % len(endings)]


def build_frames(n_phishing: int, n_legitimate: int) -> pd.DataFrame:
    rows = []
    idx = 0
    for label, n, scenarios in [("phishing_scam", n_phishing, PHISHING_SCENARIOS), ("legitimate", n_legitimate, LEGIT_SCENARIOS)]:
        for j in range(n):
            idx += 1
            bank = BANKS[j % len(BANKS)]
            scenario, action, event, destination = scenarios[j % len(scenarios)]
            frame_id = f"BV21-{label[:3].upper()}-{j+1:04d}"
            text = phishing_anchor(bank, event, destination, j) if label == "phishing_scam" else legitimate_anchor(bank, event, destination, j)
            rows.append({
                "benchmark_version": "2.1-pre-freeze",
                "frame_id": frame_id,
                "label": label,
                "scenario": scenario,
                "semantic_intent": f"banking {event} communication",
                "requested_action": action,
                "channel": "sms",
                "entity": bank,
                "destination": destination,
                "safety_state": "defanged_placeholder_only",
                "source_strategy": "researcher_authored_synthetic",
                "anchor_text": text,
                "anchor_sha256": _hash(text),
                "review_status": "not_reviewed",
                "inclusion_status": "candidate",
            })
    return pd.DataFrame(rows)


def build_jobs(frames: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for r in frames.to_dict("records"):
        for condition, definition in CONDITIONS.items():
            job = {
                **{k: r[k] for k in ["benchmark_version","frame_id","label","scenario","semantic_intent","requested_action","channel","entity","destination","safety_state"]},
                "variant_id": f"{r['frame_id']}-{condition}",
                "condition": condition,
                "condition_definition": definition,
                "anchor_text": r["anchor_text"],
                "generated_text": r["anchor_text"] if condition == "C0" else "",
                "generator_status": "not_applicable" if condition == "C0" else "not_run",
                "prompt_version": "benchmark-v2.1-dose-response-v1" if condition != "C0" else "",
                "review_status": "not_reviewed",
                "inclusion_status": "candidate",
                "exclusion_reason": "",
            }
            rows.append(job)
    return pd.DataFrame(rows)


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--phishing", type=int, default=750)
    p.add_argument("--legitimate", type=int, default=500)
    p.add_argument("--out-dir", type=Path, default=Path("data/benchmark_v2_1/full"))
    args = p.parse_args()
    args.out_dir.mkdir(parents=True, exist_ok=True)
    frames = build_frames(args.phishing, args.legitimate)
    jobs = build_jobs(frames)
    frames.to_csv(args.out_dir / "semantic_frames.csv", index=False)
    jobs.to_csv(args.out_dir / "generation_jobs.csv", index=False)
    print(f"wrote {len(frames)} frames and {len(jobs)} condition rows")

if __name__ == "__main__":
    main()
