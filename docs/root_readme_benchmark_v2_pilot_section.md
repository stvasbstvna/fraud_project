## Benchmark v2 pilot materials

The isolated non-operational Benchmark v2 pilot lives in `data/benchmark_v2/pilot/`. It contains 48 researcher-authored semantic frames, 192 unique C0–C3 variants, 144 explicitly unrun generation jobs, a detector-blinded human-review queue, provenance notes, and SHA-256 checksums.

These records are workflow-calibration material only: they are not LLM-generated, are not a licensed real-world final benchmark, remain `final_benchmark_eligible=false`, and must not be used to claim that a detector is weaker.

```powershell
.\.venv\Scripts\python.exe .\scripts\build_benchmark_v2_pilot.py
.\.venv\Scripts\python.exe .\scripts\prepare_benchmark_v2_pilot_review.py
.\.venv\Scripts\python.exe .\scripts\summarize_benchmark_v2_pilot_review.py --review-file data\benchmark_v2\pilot\pilot_review_sample.xlsx
```

Review instructions: `docs/benchmark_v2_pilot_review_instructions.md`.
