# Benchmark v2.1 — Controlled Linguistic Rewrite Robustness

**Current state: offline pipeline constructed; scientific data collection pending.** Start with `REPOSITORY_AUDIT.md`, `RESULTS.md` and `LIMITATIONS.md`. Historical v1/v2 and flat v2.1 plans/scripts/files are preserved. New canonical outputs use the nested paths requested in the task; legacy `full/` and `pilot/` stay untouched.

441 unique pending synthetic candidates; 3,087 condition slots; 441 C0 texts; 0 generated C1–C6; 0 approved/frozen rows. Target 750 phishing + 500 controls remains unachieved. The fixed candidate model is inherited, not an assertion of available provider access. No API calls, detector scoring or training occur in the offline construction.

## Reproduction

From the repository root in a **clean copy without the new materialized outputs**, run the following in order. Output files are exclusive; existing files cause an error to prevent evidence overwrite. The current workspace already contains these outputs. Do not delete or overwrite historical data for a rerun.

```powershell
.\.venv\Scripts\python.exe -m src.benchmark_v2_1.prepare_config
.\.venv\Scripts\python.exe -m src.benchmark_v2_1.build_sources
.\.venv\Scripts\python.exe -m src.benchmark_v2_1.build_frames
.\.venv\Scripts\python.exe -m src.benchmark_v2_1.review_sources
.\.venv\Scripts\python.exe -m src.benchmark_v2_1.generate_variants --dry-run
.\.venv\Scripts\python.exe -m src.benchmark_v2_1.validate_variants
.\.venv\Scripts\python.exe -m src.benchmark_v2_1.measure_distances
.\.venv\Scripts\python.exe -m src.benchmark_v2_1.build_review_queue
.\.venv\Scripts\python.exe -m src.benchmark_v2_1.freeze_benchmark --pending
.\.venv\Scripts\python.exe -m src.benchmark_v2_1.analyze
.\.venv\Scripts\python.exe -m src.benchmark_v2_1.make_figures
.\.venv\Scripts\python.exe -m src.benchmark_v2_1.audit_runtime
.\.venv\Scripts\python.exe -m pytest -q --basetemp .pytest_cache/v21-reproduction-unique
```

`freeze_benchmark --pending` creates an explicit empty frozen schema and PENDING manifest, not a scientifically frozen dataset. `evaluate` refuses that status. Later commands, only after source review, eligible external generation, completed independent variant review and manipulation validation, are:

```powershell
.\.venv\Scripts\python.exe -m src.benchmark_v2_1.generate_variants --frames PATH_TO_REVIEWED_PILOT --responses RAW_RESPONSE_ENVELOPES.jsonl --output data/benchmark_v2_1/generated/pilot_responses.csv
.\.venv\Scripts\python.exe -m src.benchmark_v2_1.evaluate
```

Actual source review, source-family contamination control, pilot signoff, assembling C0 with accepted response rows into a complete matrix, and a separate final freeze are still required before evaluation. Do not bypass pending gates by renaming a file. `--input`/`--reviews` on freeze accept explicit completed artifacts; schema-only outputs must remain archived when constructing a later run.

Import source decisions using `review_sources --reviews data/benchmark_v2_1/review/source_review_completed.csv`; this produces `source/frames_reviewed.csv` and does not approve rows lacking two content-bound human decisions. Select the eligible pilot prospectively from that file. `generate_variants --frames ... --source-reviews ... --dry-run` verifies those decisions before preparing requests. After external execution, `assemble_matrix --frames ... --responses ...` preserves C0 and requires all six responses per frame. Run distance/review stages with `--input` pointing to that assembled matrix. Real freeze additionally requires `--frames`, `--source-reviews`, `--responses` (retained raw JSONL), `--input` and `--reviews` evidence; it verifies exact prompt/request/model/response metadata and input-bound manipulation evidence.

## Files and status

- `source/frames.csv`: unique candidates, all pending; original source IDs retained.
- `generated/variant_matrix.csv`: slots, not generated responses; `dry_run.json` records zero eligible requests.
- `generated/distance_measurements.csv`: only completed C0 text measurements, no prediction fields populated.
- `review/review_queue.csv`, `adjudication.csv`, `review_summary.json`: blank independent review assignments/status.
- `frozen/benchmark_v2_1.csv`, `manifest.json`: empty schema/PENDING.
- `results/benchmark_v2_1/tables/`: Table A pending composition; B–F schema/NOT RUN.
- `results/benchmark_v2_1/figures/figure_status.json`: planned graph explanations, no fabricated empirical image.
- `results/benchmark_v2_1/PRESENTATION_SUMMARY.md`: safe presentation statements and explicit limits.

See `IMPLEMENTATION_PLAN.md`, `DATA_PROVENANCE.md`, `PROMPT_DESIGN.md`, `METHODOLOGY.md`, `STATISTICAL_ANALYSIS_PLAN.md`, `HUMAN_REVIEW_PROTOCOL.md`, `FROZEN_MODEL_CARD.md`, `LIMITATIONS.md`, `RESULTS.md` and `ENGINEERING_REPORT.md`.
