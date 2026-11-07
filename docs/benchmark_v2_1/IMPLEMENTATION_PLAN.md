# Benchmark v2.1 implementation plan

**Goal:** Add a defensible offline-first seven-condition pipeline without altering historical evidence.

**Spec:** User-supplied 28-section request, received 2026-11-06; `REPOSITORY_AUDIT.md` records current constraints. Python/pandas/sklearn/joblib/scipy/matplotlib already used by this repository.

**Architecture:** New `src/benchmark_v2_1/` modules own canonical source, generation, review, freeze, evaluation and reporting stages. Historic scripts, plans and results remain read-only. New pending artifacts are genuine empty/status outputs, never simulated results. The detailed user execution instruction supplies the implementation scope; no additional design choice is delegated to the user.

**Approaches considered:** Repairing flat old scripts would change earlier protocol evidence; replacing sources with automatically imported collections would mix labels/licenses. Additive canonical pipeline is selected because it preserves evidence and makes unresolved review visible. Synthetic candidates are quarantined, not accepted merely to achieve 1,250 frames.

## Tasks and interfaces

- [ ] Inventory and audit sources; snapshot existing bytes. `audit.py` produces inventory/counts and preservation check. Never read `.env`.
- [ ] Add tests first for stable IDs, deduplication, source eligibility, structured validation, preserved placeholders/entities/actions/labels, no operational destinations, no detector leakage, strict complete sets, invalid probabilities, review binding, write confinement and preservation.
- [ ] `sources.py`: `canonical_frames(DataFrame) -> (frames, duplicates)`; stable content hashes, pending candidate status. `build_frames` CLI imports only old synthetic candidates; actual-source acceptance requires provenance, licensing, language/channel/banking and manual label checks.
- [ ] `generation.py`: exact condition prompts/schema/config; allowlisted payload; dry-run request manifest for approved frames only; external structured response ingestion with full metadata and request hashes. No model substitution; actual API execution remains pending until source review and provider readiness. No generated text fabricated.
- [ ] `review.py`: objective validation separately from manual findings; CSV queue/adjudication; only two independently approved, content-bound reviews satisfy a freeze gate. Action/intent equivalence is human evidence, not string inference.
- [ ] `freeze.py`: exact seven conditions, invariant fields, all reviews, no duplicates/live endpoints, verified model hashes; immutable CSV and manifest, empty pending schema when no eligible frames. C0 equals defanged source text, raw source preserved separately.
- [ ] `evaluate.py`: only frozen/hash-verified rows; frozen models `predict_proba`/`predict` only; frozen vectorizer cosine and prespecified equal-weight composite, no fit. Separate LR/RF representations.
- [ ] `analysis.py`, `reports.py`: strict paired inputs, seven Holm tests on frame slopes/contrasts, frame bootstrap CI, tables A–F and figures 1–5; explicit NOT RUN manifests when data unavailable. Median-absolute-shift representative example rule, never maximum effect. No false-positive claim without reviewed controls.
- [ ] Run offline build/dry run/review/pending freeze, full existing plus new tests, preservation verification; record actual status and exact commands in documentation.

## Review focus

Wrong condition with correct row count; duplicate source templates across IDs; altered reviewed text; approvals without semantic fields; bare domains/phone/email endpoints; out-of-range or nonfinite predictions; class-order assumptions; no-control denominators; zero distance/zero-variance inference; overwritten historical outputs. Each must fail explicitly or remain PENDING, never silently pass.

## Boundaries

No network generation, detector evaluation of pending frames, source scraping with automatic labels, retraining, fabricated review, or publication. Target 750/500 remains a target. Archived primary family/power results are not silently reused as evidence for revised representation. Run native implementation in this workspace because extensive existing untracked artifacts would be missing from a new checkout; all new writes are confined to new paths.

## Execution ledger

Offline implementation and materialization completed: canonical candidates/dedup diagnostics, six exact prompts, inactive config, request/response adapter, source and variant review forms/import, complete matrix assembly, strict freeze/evaluation gates, distance/inference/report modules. Independent code review findings were fixed with regression tests. Final suite: 147 passed; original 360 file hashes unchanged. Scientific stages remain pending: external row-level source audit, source semantic approval and independent family sampling, actual generation, pilot/variant review and manipulation validation, real freeze/evaluation/analysis. The unchecked phase descriptions above do not imply those scientific activities were completed. See ENGINEERING_REPORT.md for exact counts and limitations.
