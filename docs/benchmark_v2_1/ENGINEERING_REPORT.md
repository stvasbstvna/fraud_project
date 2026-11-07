# Engineering and research report — 2026-11-06

## 1. What existed

Historical mixed source collections, a final SMS split, two fitted detectors, v1 paired rewrite observations/reviews/dashboard/figures, earlier C0–C3 v2 planning, and a C0–C6 v2.1 synthetic planning package. Existing v2.1 full/pilot were ungenerated/unreviewed, with duplicate templates and intent/action validity problems. Details and exact evidence paths: `REPOSITORY_AUDIT.md`.

## 2. What changed

Added a separate canonical pipeline in `src/benchmark_v2_1/`, versioned nested configs/prompts, pending source/variant review artifacts, deduplicated candidate sources, strict freeze/evaluation/inference/reporting code, and the requested nested documentation. No existing source, model, v1/v2 result, old flat v2.1 script/config or legacy full/pilot data was modified. No dependency installation, commit, push, publication, email, external data import or API generation occurred.

## 3. Exact file ledger

`ADDED_FILES.csv` lists the 80 added non-cache project files by exact relative path/size (the ledger itself is the 81st addition and is excluded from its own size inventory). `BASELINE_INVENTORY.csv` records the original 360 files and hashes; final comparison found **0 changed/missing baseline files**. Main additions:

- `src/benchmark_v2_1/__init__.py`, `core.py`, `build_sources.py`, `build_frames.py`, `prepare_config.py`, `generate_variants.py`, `validate_variants.py`, `measure_distances.py`, `review_sources.py`, `assemble_matrix.py`, `build_review_queue.py`, `freeze_benchmark.py`, `evaluate.py`, `statistics.py`, `analyze.py`, `reports.py`, `make_figures.py`, `audit_runtime.py`.
- `tests/benchmark_v2_1/test_pipeline.py`, `test_analysis.py`, `test_provenance.py`, `test_freeze_cli.py`, `test_review_import.py`.
- `configs/benchmark_v2_1/source_registry.csv`, `benchmark_config.yaml`, `generator_config.json`, `PROMPT_REGISTRY.md` and six exact C1–C6 prompt files.
- `data/benchmark_v2_1/source/frames.csv`, `pilot_candidates.csv`, `source_audit.json`, `build_summary.json`; `generated/variant_matrix.csv`, `dry_run.json`, `distance_measurements.csv`; `review/review_queue.csv`, `source_review_queue.csv`, `adjudication.csv`, `review_summary.json`; `frozen/benchmark_v2_1.csv`, `manifest.json`.
- `results/benchmark_v2_1/tables/A_dataset_composition.csv/.md` through `F_probability_changes.csv/.md`; `figures/figure_status.json`; `diagnostics/exact_duplicates.csv`, `near_duplicates.csv`, `variant_validation.csv`, `manipulation_check.json`, `analysis_status.json`, `runtime_audit.json`; `PRESENTATION_SUMMARY.md`.
- New nested documentation: README, REPOSITORY_AUDIT, DATA_PROVENANCE, FROZEN_MODEL_CARD, PROMPT_DESIGN, METHODOLOGY, STATISTICAL_ANALYSIS_PLAN, HUMAN_REVIEW_PROTOCOL, LIMITATIONS, RESULTS, IMPLEMENTATION_PLAN, this report and inventories.

## 4–5. Source evaluation and decisions

Twelve registry entries cover synthetic legacy candidates; Mendeley; SmishTank; Gateway; SpamHunter; Super SMS; SmishX; UCI; ExAIS; NUS; multilingual collections; email collections. Original-source documentation and licensing evidence are linked in `DATA_PROVENANCE.md`.

**Accepted external sources for generation/evaluation: zero.** Mendeley (explicit CC BY 4.0) and Gateway (MIT repository; scope review pending) are priority candidates. UCI (CC BY 4.0) is a possible reviewed-control source, never automatic phishing from spam. SmishTank/SpamHunter/Super/ExAIS/NUS remain on hold for license, label and row-level provenance checks. SmishX/SmishTank overlap existing training sources; contamination control is mandatory. Multilingual/email collections are excluded from the primary population because language/channel differ. No source was bulk imported from the aggregator. Row-level source audits are still incomplete.

## 6–7. Exact counts

| Artifact | Frames | Condition slots | Populated C0 | Generated C1–C6 | Frozen rows |
|---|---:|---:|---:|---:|---:|
| Preserved legacy full | 1,250 rows / 441 unique texts | 8,750 | 1,250 | 0 | 0 |
| Preserved legacy pilot | 48 rows / 36 unique texts | 336 | 48 | 0 | 0 |
| New canonical candidates | 441 unique texts | 3,087 | 441 | 0 | 0 |
| New distinct pilot candidates | 48 (24/24) | not separately materialized | 48 source anchors | 0 | 0 |

Canonical candidate labels: 254 phishing-labelled/187 legitimate-labelled, **not validated ground truth**. 809 duplicate excess legacy rows removed from canonical selection, retained in diagnostics. 22,406 within-entity near-duplicate pairs at ≥0.90 remain. Eligible source frames: 0. Target 750/500 and 8,750 complete rows remains PENDING.

## 8–9. Generation and human review

Six exact prompts and fixed inactive candidate config prepared. Candidate `gpt-5.4-mini-2026-03-17` availability/access not verified; no substitution. Dry run: 48 candidate frames, 0 eligible requests, **0 API calls**. External structured execution/ingestion adapter exists; automatic provider execution is not enabled or claimed complete.

882 source-review assignments plus 882 C0 variant-review assignments are blank; these are separate tasks, not 1,764 distinct messages. Zero approvals, zero adjudications, agreement NOT AVAILABLE. No rewrite text/review was fabricated. Source decisions bind all controlled metadata; variant decisions bind exact text. Freeze requires complete approved conditions, two independent reviewers, source evidence, raw response/request/prompt hashes and matrix-bound manipulation validation. Real-world source selection and human pilot signoff remain external work.

## 10. Frozen detectors

Both actual model SHA-256 hashes match historical records. Actual class labels [0,1], threshold 0.5, 3,715-feature vocabulary each, identical vocabulary and IDF hashes. Full actual parameters in runtime audit and `FROZEN_MODEL_CARD.md`. No retraining or new prediction. The evaluator was invoked and correctly refused the PENDING freeze (expected nonzero exit, no scoring). Historical fit-data byte identity is not retroactively proven by current hashes.

## 11. Statistical results

New empirical statistical results: **NOT RUN**. Pipeline implements seven frame-level tests/contrasts with Holm correction, validated finite predictions, frame bootstrap intervals, zero-variance/insufficient-data reporting and strict paired completeness. New metric version uses fitted detector vectorizers; old refitted-space power simulations cannot be claimed as validation. Template-family dependence must be resolved prospectively before scientific confirmatory release. Numeric condition order is not assumed to be a valid equal-spaced dose.

## 12. Limitations

No completed data generation/review/evaluation. Invalid/ambiguous candidate intent, template dependence and entity/scenario confounding remain; an exact-deduplicated CSV does not cure them. External row-level audits, training/template overlap screening, sampling, final attrition assumptions and pilot signoff are unresolved. Source ingestion beyond legacy synthetic data is not implemented as automatic acceptance. No observed graphs B–F/1–5 can be produced yet. See `LIMITATIONS.md`.

## 13. Tests and review

Baseline: 109 passed. Final: **147 passed in 5.66s**, command below. Initial temp-directory fixture errors were environmental and resolved by workspace-local `--basetemp`; tests were not weakened. New safety/provenance tests were observed failing before implementation/fixes. Independent reviewer identified missing json import, source-quarantine bypass, transferable manipulation evidence and insufficient generation provenance. All four were corrected and covered; successful full non-pending freeze is exercised with isolated **test fixtures**, not research observations.

No failing tests remain. Broader scientific incompleteness is explicitly pending and is not hidden by the green suite. Read-only baseline SHA-256 comparison: 360/360 unchanged.

## 14. Reproduction

Full stage commands and exclusive-output handling: `README.md`. The offline execution ran configuration → source registry → dedup frames → dry run → objective validation → frozen-vectorizer distance → blank reviews → PENDING freeze → NOT RUN analysis → pending tables/figures → runtime audit. Source review forms were exported separately. Reproduce materialization in a clean isolated copy without the newly created outputs; occupied output paths fail safely.

```powershell
.\.venv\Scripts\python.exe -m pytest -q --basetemp .pytest_cache/v21-final-tests-20261106
.\.venv\Scripts\python.exe -m src.benchmark_v2_1.evaluate
```

First command: 147 passed. Second command: expected refusal `NOT RUN: benchmark is PENDING human/source review and generation`. Run read-only inventory hash comparison to verify old evidence, or inspect `runtime_audit.json`.

## 15–16. Symposium claims

Safe: research question, prospective controlled design, audit findings, counts clearly called candidate/slot counts, unchanged detector identities, and verified historical v1 observations explicitly labeled prior. V1 143 phishing pairs show ~0.6993 percentage-point recall drop per detector; exact McNemar p=1.0. UNIONBANK LR 0.5653773212→0.4898664850 is a saved prior illustration, not a new representative outcome.

Do NOT present 8,750 generated rows, approved v2.1 labels, completed pilot validation, new score changes/significance, linguistic causality, generalized detector vulnerability or confirmed source redistribution permission. `results/benchmark_v2_1/PRESENTATION_SUMMARY.md` explains planned graph axes and these evidence boundaries.

## Implementation rulings

Additive canonical namespace protects extensive untracked historical work; working in a clean git checkout would omit it. Canonical source labels remain pending despite legacy approval prose because actual texts do not establish intent. TF-IDF distance is explicitly versioned to the requested frozen representation; the old protocol/power files are preserved rather than silently reinterpreted. Placeholder identity and exact source/review binding take precedence over achieving target N. These conservative choices cost incomplete current data; approving questionable labels or fabricated generations would invalidate the benchmark.
