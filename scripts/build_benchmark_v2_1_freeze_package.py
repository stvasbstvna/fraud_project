"""Build a hash manifest for Benchmark v2.1 pre-freeze artifacts."""
from __future__ import annotations
import hashlib, json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
FILES=[
"configs/benchmark_v2_1_generator.yaml",
"docs/benchmark_v2_1_protocol_FINAL_CANDIDATE.md",
"docs/benchmark_v2_1_research_decisions_FINAL.md",
"docs/benchmark_v2_1_prompt_package_FINAL.md",
"docs/benchmark_v2_1_pilot_review_instructions_FINAL.md",
"docs/benchmark_v2_1_distance_metrics.md",
"docs/benchmark_v2_1_confirmatory_family_decision.md",
"docs/frozen_detector_representation.md",
"data/benchmark_v2_1/source_manifest.csv",
"data/benchmark_v2_1/pilot/semantic_frames.csv",
"data/benchmark_v2_1/pilot/generation_jobs.csv",
"data/benchmark_v2_1/full/semantic_frames.csv",
"data/benchmark_v2_1/full/generation_jobs.csv",
"analysis/benchmark_v2_1_distance_metrics.py",
"analysis/benchmark_v2_1_confirmatory_analysis.py",
"scripts/check_benchmark_v2_1_freeze_readiness.py",
"scripts/run_benchmark_v2_1_generation.py",
]
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    manifest={"benchmark_version":"2.1-pre-freeze","status":"NOT_FULLY_FROZEN_HUMAN_REVIEW_AND_GENERATION_PENDING","files":[]}
    for rel in FILES:
        p=ROOT/rel
        manifest["files"].append({"path":rel,"exists":p.exists(),"sha256":sha(p) if p.exists() else None})
    out=ROOT/"results/benchmark_v2_1/freeze/FREEZE_MANIFEST.json"; out.parent.mkdir(parents=True,exist_ok=True); out.write_text(json.dumps(manifest,indent=2),encoding="utf-8"); print(out)
if __name__=="__main__": main()
