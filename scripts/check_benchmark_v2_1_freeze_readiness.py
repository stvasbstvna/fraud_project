"""Conservative Benchmark v2.1 freeze-readiness gate.

This checker reports objective file/integrity state separately from external
human-review and generation gates. It does not infer approval from prose.
"""
from __future__ import annotations
from pathlib import Path
import hashlib
import json
import pandas as pd

ROOT=Path(__file__).resolve().parents[1]

REQUIRED=[
    "configs/benchmark_v2_1_generator.yaml",
    "docs/benchmark_v2_1_protocol_FINAL_CANDIDATE.md",
    "docs/benchmark_v2_1_research_decisions_FINAL.md",
    "docs/benchmark_v2_1_prompt_package_FINAL.md",
    "docs/benchmark_v2_1_pilot_review_instructions_FINAL.md",
    "docs/benchmark_v2_1_confirmatory_analysis_plan_FINAL.md",
    "configs/benchmark_v2_1_confirmatory_family.yaml",
    "analysis/benchmark_v2_1_confirmatory_analysis.py",
    "analysis/benchmark_v2_1_power_simulation.py",
    "results/benchmark_v2_1/power/power_summary.json",
    "data/benchmark_v2_1/source_manifest.csv",
    "data/benchmark_v2_1/pilot/semantic_frames.csv",
    "data/benchmark_v2_1/pilot/generation_jobs.csv",
    "data/benchmark_v2_1/full/semantic_frames.csv",
    "data/benchmark_v2_1/full/generation_jobs.csv",
]

def main():
    blockers={}
    blockers["missing_required_artifacts"]=sum(not (ROOT/p).exists() for p in REQUIRED)
    jobs=ROOT/"data/benchmark_v2_1/full/generation_jobs.csv"
    if jobs.exists():
        df=pd.read_csv(jobs).fillna("")
        blockers["frame_condition_errors"]=int((df.groupby("frame_id").condition.nunique()!=7).sum())
        blockers["duplicate_variant_ids"]=int(df.variant_id.duplicated().sum())
        blockers["unsafe_live_urls"]=int(df.anchor_text.astype(str).str.contains(r"https?://",regex=True).sum())
        blockers["generation_pending"]=int(df.generator_status.eq("not_run").any())
        blockers["full_scale_errors"]=int(len(df)!=8750 or df.frame_id.nunique()!=1250)
    else:
        blockers.update(frame_condition_errors=1,duplicate_variant_ids=1,unsafe_live_urls=1,generation_pending=1,full_scale_errors=1)
    pilot_jobs=ROOT/"data/benchmark_v2_1/pilot/generation_jobs.csv"
    if pilot_jobs.exists():
        pilot=pd.read_csv(pilot_jobs).fillna("")
        blockers["pilot_condition_errors"]=int(len(pilot)!=336 or pilot.frame_id.nunique()!=48 or (pilot.groupby("frame_id").condition.nunique()!=7).any())
    else:
        blockers["pilot_condition_errors"]=1
    manifest_path=ROOT/"data/benchmark_v2_1/source_manifest.csv"
    blockers["source_manifest_errors"]=1
    if manifest_path.exists():
        sources=pd.read_csv(manifest_path).fillna("")
        required_source={"source_id","source_file","allowed_for_generation","transformation_permission","privacy_review_status","source_sha256"}
        if required_source.issubset(sources.columns):
            synth=sources[sources.source_id.eq("SYNTH-V21")]
            if len(synth)==1:
                row=synth.iloc[0]; source=ROOT/str(row.source_file)
                digest=hashlib.sha256(source.read_bytes()).hexdigest() if source.exists() else ""
                blockers["source_manifest_errors"]=int(not (
                    row.allowed_for_generation=="yes" and row.transformation_permission=="permitted"
                    and row.privacy_review_status=="passed" and digest==row.source_sha256
                ))
    # These are intentionally external gates. They can only be cleared by imported
    # completed review/generation artifacts, never by changing this checker.
    pilot_review=ROOT/"data/benchmark_v2_1/review/pilot_review_completed.csv"
    final_review=ROOT/"data/benchmark_v2_1/review/full_review_completed.csv"
    blockers["pilot_human_review_pending"]=0 if pilot_review.exists() else 1
    blockers["final_human_review_pending"]=0 if final_review.exists() else 1
    final_dataset=ROOT/"data/benchmark_v2_1/final/benchmark_v2_1_final.csv"
    blockers["final_dataset_pending"]=0 if final_dataset.exists() else 1

    family_path=ROOT/"configs/benchmark_v2_1_confirmatory_family.yaml"
    blockers["confirmatory_analysis_plan_conflict"] = 1
    if family_path.exists():
        import yaml
        family=yaml.safe_load(family_path.read_text(encoding="utf-8"))
        ids=[item["id"] for item in family.get("hypotheses",[])]
        plan=(ROOT/"docs/benchmark_v2_1_confirmatory_analysis_plan_FINAL.md").read_text(encoding="utf-8")
        analysis=(ROOT/"analysis/benchmark_v2_1_confirmatory_analysis.py").read_text(encoding="utf-8")
        power_path=ROOT/"results/benchmark_v2_1/power/power_summary.json"
        power=json.loads(power_path.read_text(encoding="utf-8")) if power_path.exists() else {}
        protocol=(ROOT/"docs/benchmark_v2_1_protocol_FINAL_CANDIDATE.md").read_text(encoding="utf-8")
        consistent=(len(ids)==7 and len(set(ids))==7 and all(hid in plan for hid in ids)
                    and "configs/benchmark_v2_1_confirmatory_family.yaml" in analysis
                    and power.get("hypothesis_ids")==ids and power.get("hypothesis_count")==7
                    and family.get("family_version") in protocol
                    and "750" in protocol and "500" in protocol)
        blockers["confirmatory_analysis_plan_conflict"] = int(not consistent)
    manipulation=ROOT/"results/benchmark_v2_1/pilot/manipulation_check.json"
    blockers["pilot_manipulation_pending_or_failed"] = 1
    if manipulation.exists():
        state=json.loads(manipulation.read_text(encoding="utf-8"))
        required=("semantic_preservation_passed","requested_action_preservation_passed","c3_less_direct_passed","distance_ordering_passed","c6_high_distance_passed","human_review_quality_passed")
        blockers["pilot_manipulation_pending_or_failed"] = int(not all(state.get(key) is True for key in required))
    technical_keys=["missing_required_artifacts","frame_condition_errors","duplicate_variant_ids","unsafe_live_urls","full_scale_errors","pilot_condition_errors","source_manifest_errors","confirmatory_analysis_plan_conflict"]
    technical_ready=all(blockers[k]==0 for k in technical_keys)
    full_ready=all(v==0 for v in blockers.values())
    status="FULL_FREEZE_READY" if full_ready else ("TECHNICAL_FREEZE_READY_EXTERNAL_ACTIONS_PENDING" if technical_ready else "BLOCKED_NOT_TECHNICALLY_READY")
    report={"benchmark_version":"2.1-pre-freeze","status":status,"technical_ready":technical_ready,"full_ready":full_ready,"blockers":blockers}
    out=ROOT/"results/benchmark_v2_1/freeze/readiness.json"; out.parent.mkdir(parents=True,exist_ok=True); out.write_text(json.dumps(report,indent=2),encoding="utf-8")
    print("BENCHMARK V2.1 FREEZE READINESS\n===============================")
    for k,v in blockers.items(): print(f"{k:34s} {v}")
    print(f"\nSTATUS: {status}")
if __name__=="__main__": main()
