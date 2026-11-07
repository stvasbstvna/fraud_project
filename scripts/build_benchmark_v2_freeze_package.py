"""Build a deterministic Benchmark v2 pre-generation freeze-readiness package.

This script does not generate messages, call an API, run detectors, or authorize
generation. It snapshots and hashes the methodological inputs and identifies
unresolved decisions that prevent a defensible final freeze.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import shutil
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.benchmark_v2_power_analysis import approximate_mcnemar_scenarios, wilson_half_width


DEFAULT_OUTPUT = ROOT / "data/benchmark_v2/freeze_candidate"
INPUTS = [
    "docs/benchmark_v2_protocol.md",
    "docs/benchmark_v2_hypotheses.md",
    "docs/benchmark_v2_analysis_plan.md",
    "docs/benchmark_v2_power_analysis.md",
    "docs/benchmark_v2_prompt_package_draft.md",
    "docs/benchmark_v2_review_rubric.md",
    "docs/benchmark_v2_pilot_review_instructions.md",
    "docs/benchmark_v2_provenance_and_ethics.md",
    "docs/benchmark_v2_decision_matrix.md",
    "docs/benchmark_v2_source_authorization_decision.md",
    "docs/benchmark_v2_power_decision.md",
    "docs/benchmark_v2_pilot_review_completion_checklist.md",
    "docs/benchmark_v2_draft_transition.md",
    "docs/benchmark_v2_freeze_signoff.md",
    "docs/benchmark_v2_FINAL_DECISION_PACKAGE.md",
    "docs/benchmark_v2_faculty_decision_request.md",
    "docs/benchmark_v2_researcher_actions.md",
    "configs/benchmark_v2.yaml",
    "configs/benchmark_v2_freeze_register.yaml",
    "configs/benchmark_v2_generator.yaml",
    "data/benchmark_v2/source_manifest.csv",
    "schemas/benchmark_v2_semantic_frame.schema.json",
    "schemas/benchmark_v2_variant.schema.json",
    "schemas/benchmark_v2_review.schema.json",
    "schemas/benchmark_v2_source_manifest.schema.json",
    "src/validate_benchmark_v2.py",
    "src/benchmark_v2_power_analysis.py",
    "analysis/benchmark_v2_power_simulation.py",
    "scripts/check_benchmark_v2_freeze_readiness.py",
]
PLANNING_ASSUMPTIONS = {
    "baseline_recall": 0.98,
    "minimum_meaningful_paired_recall_difference": 0.04,
    "discordant_pair_rate": 0.10,
    "familywise_alpha": 0.05,
    "confirmatory_tests": 7,
    "conservative_per_test_alpha_for_planning": 0.05 / 7,
    "target_power": 0.80,
    "candidate_confirmatory_phishing_scenarios": 1000,
    "candidate_confirmatory_legitimate_scenarios": 500,
    "variants_per_scenario": 4,
    "candidate_quality_validation_scenarios": 120,
    "existing_prompt_development_pilot_scenarios": 48,
}


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def scan_tbd(path: Path) -> list[dict[str, object]]:
    issues = []
    for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if re.search(r"\bTBD(?:_[A-Z0-9_]+)?\b", line):
            issues.append({"file": path.relative_to(ROOT).as_posix(), "line": number, "text": line.strip()})
    return issues


def build_power_snapshot() -> dict[str, object]:
    a = PLANNING_ASSUMPTIONS
    required = approximate_mcnemar_scenarios(
        a["minimum_meaningful_paired_recall_difference"],
        a["discordant_pair_rate"],
        a["conservative_per_test_alpha_for_planning"],
        a["target_power"],
    )
    phishing = a["candidate_confirmatory_phishing_scenarios"]
    legitimate = a["candidate_confirmatory_legitimate_scenarios"]
    return {
        "status": "candidate_conservative_bound_not_final_power_freeze",
        "assumptions": a,
        "approximate_required_phishing_scenarios": required,
        "candidate_total_confirmatory_scenarios": phishing + legitimate,
        "candidate_total_confirmatory_variants": (phishing + legitimate) * a["variants_per_scenario"],
        "candidate_total_quality_variants": a["candidate_quality_validation_scenarios"] * a["variants_per_scenario"],
        "recall_wilson_half_width_at_candidate_phishing_n": wilson_half_width(phishing, a["baseline_recall"], a["familywise_alpha"]),
        "specificity_wilson_half_width_at_candidate_legitimate_n_and_0_90": wilson_half_width(legitimate, 0.90, a["familywise_alpha"]),
        "required_before_final_freeze": "Exact scenario-level simulation of the seven-test Holm family, H2 paired indicators, detector dependence, and complete-set attrition.",
    }


def readiness_report() -> dict[str, object]:
    config = yaml.safe_load((ROOT / "configs/benchmark_v2.yaml").read_text(encoding="utf-8"))
    register = yaml.safe_load((ROOT / "configs/benchmark_v2_freeze_register.yaml").read_text(encoding="utf-8"))
    tbd = []
    for relative in ("configs/benchmark_v2.yaml", "configs/benchmark_v2_freeze_register.yaml", "docs/benchmark_v2_prompt_package_draft.md"):
        tbd.extend(scan_tbd(ROOT / relative))
    entries = config.get("generation", {}).get("generator_pool", {}).get("entries", [])
    active = [entry for entry in entries if entry.get("status") == "active" and float(entry.get("assignment_weight", 0)) > 0]
    outputs = config.get("outputs", {})
    final_sources = ROOT / outputs.get("source_manifest", "data/benchmark_v2/source_manifest.jsonl")
    blockers = []
    if tbd:
        blockers.append({"code": "unresolved_tbd", "count": len(tbd), "detail": "Configuration, prompt, or freeze-register decisions remain TBD."})
    if not active:
        blockers.append({"code": "no_active_generator_block", "detail": "No versioned generator block has active status and positive assignment weight."})
    if not final_sources.exists():
        blockers.append({"code": "missing_authorized_source_manifest", "detail": str(final_sources.relative_to(ROOT)).replace("\\", "/")})
    prompt_status = str(register.get("benchmark_v2_pre_generation_freeze", {}).get("status", ""))
    if "DO_NOT_GENERATE" in prompt_status:
        blockers.append({"code": "generation_prohibited_by_freeze_register", "detail": prompt_status})
    config_text = (ROOT / "configs/benchmark_v2.yaml").read_text(encoding="utf-8").casefold()
    prompt_text = (ROOT / "docs/benchmark_v2_prompt_package_draft.md").read_text(encoding="utf-8").casefold()
    pilot_text = "\n".join([
        (ROOT / "scripts/build_benchmark_v2_pilot.py").read_text(encoding="utf-8"),
        (ROOT / "docs/benchmark_v2_pilot_review_instructions.md").read_text(encoding="utf-8"),
    ]).casefold()
    pilot_more_explicit = "more explicit" in pilot_text or "clearer request" in pilot_text or "explicit request" in pilot_text
    if ("explicitness_reduction" in config_text or "explicitness lower" in config_text or "softened" in config_text) and pilot_more_explicit:
        blockers.append({"code": "c3_direction_conflict", "detail": "Main config specifies softened/lower C3 explicitness while the implemented pilot specifies a more explicit review/open request."})
    if "draft" in prompt_text[:500]:
        blockers.append({"code": "prompt_package_is_draft", "detail": "Prompt text has not been signed off and version-frozen."})
    exact_power = ROOT / "results/benchmark_v2/power/power_summary.json"
    if not exact_power.exists():
        blockers.append({"code": "exact_power_simulation_pending", "detail": "The required seven-test Holm-family simulation has not been run."})
    else:
        power_state = json.loads(exact_power.read_text(encoding="utf-8"))
        if power_state.get("status") != "confirmatory_assumptions_frozen":
            blockers.append({"code": "confirmatory_power_assumptions_pending", "detail": "The exact seven-test framework and sensitivity table exist, but final effects, dependence, attrition, and target-power assumptions require approval."})
    return {
        "status": "BLOCKED_NOT_FROZEN" if blockers else "READY_FOR_SIGNOFF_NOT_AUTHORIZED",
        "generation_authorized": False,
        "message_generation_performed": False,
        "api_called": False,
        "detectors_run": False,
        "blockers": blockers,
        "unresolved_tbd_locations": tbd,
        "required_signoffs": ["methodology_owner", "data_provenance_owner", "human_review_lead"],
    }


def build_package(output_dir: Path = DEFAULT_OUTPUT) -> dict[str, object]:
    output_dir.mkdir(parents=True, exist_ok=True)
    inputs = {relative: sha256(ROOT / relative) for relative in INPUTS}
    power = build_power_snapshot()
    readiness = readiness_report()
    prompt_source = ROOT / "docs/benchmark_v2_prompt_package_draft.md"
    prompt_snapshot = output_dir / "prompt_package_snapshot_DRAFT_NOT_FROZEN.md"
    shutil.copyfile(prompt_source, prompt_snapshot)
    (output_dir / "power_planning_snapshot.json").write_text(json.dumps(power, indent=2) + "\n", encoding="utf-8")
    (output_dir / "freeze_readiness_report.json").write_text(json.dumps(readiness, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    authorization = {
        "status": readiness["status"], "generation_authorized": False,
        "reason": "Generation remains prohibited until every readiness blocker is resolved and all required signoffs are recorded.",
    }
    (output_dir / "generation_authorization.json").write_text(json.dumps(authorization, indent=2) + "\n", encoding="utf-8")
    blocker_lines = "\n".join(f"- `{item['code']}` — {item['detail']}" for item in readiness["blockers"])
    markdown = f"""# Benchmark v2 freeze-readiness report

**Status: `{readiness['status']}`**  
**Generation authorized: no**

This deterministic package snapshots the current protocol, prompts, configuration, schemas, validator, and power utility. It does not generate messages, call an API, run detectors, or make Benchmark v2 eligible for evaluation.

## Blocking decisions

{blocker_lines}

## Candidate scale for planning only

- Confirmatory phishing scenarios: {PLANNING_ASSUMPTIONS['candidate_confirmatory_phishing_scenarios']}
- Confirmatory legitimate scenarios: {PLANNING_ASSUMPTIONS['candidate_confirmatory_legitimate_scenarios']}
- Confirmatory variants at four conditions: {power['candidate_total_confirmatory_variants']}
- Quality-validation scenarios: {PLANNING_ASSUMPTIONS['candidate_quality_validation_scenarios']} (excluded from confirmatory inference)
- Existing 48-scenario prompt-development pilot: excluded from Benchmark v2 inference
- Conservative approximate phishing requirement: {power['approximate_required_phishing_scenarios']} scenarios under the recorded assumptions

The candidate scale is not a final sample-size authorization. Exact simulation and complete-set attrition planning remain required.
"""
    (output_dir / "freeze_readiness_report.md").write_text(markdown, encoding="utf-8")
    package_files = ["prompt_package_snapshot_DRAFT_NOT_FROZEN.md", "power_planning_snapshot.json", "freeze_readiness_report.json", "freeze_readiness_report.md", "generation_authorization.json"]
    manifest = {
        "package_version": "0.1.0-freeze-candidate",
        "status": readiness["status"], "generation_authorized": False,
        "input_sha256": inputs,
        "package_file_sha256": {name: sha256(output_dir / name) for name in package_files},
    }
    (output_dir / "freeze_manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    return {"status": readiness["status"], "blockers": len(readiness["blockers"]), "output": str(output_dir)}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    print(json.dumps(build_package(args.output_dir), indent=2))


if __name__ == "__main__":
    main()
