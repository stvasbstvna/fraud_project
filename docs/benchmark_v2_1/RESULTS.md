# Evidence status — 2026-11-06

## Prior v1: saved observations, not new v2.1 results

`results/rewrite_experiment/statistical_tests.csv` contains 143 phishing pairs. LR recall 98.6014% → 97.9021%; RF 97.9021% → 97.2028%. Each net drop is 0.6993 percentage points, one detected→missed and zero reverse changes. Exact paired McNemar p=1.0 for each. Do not claim a statistically established overall reduction. Saved run summary identifies 153 eligible total pairs and required review; this audit verified the files rather than rerunning historical inference.

UNIONBANK `BRW-0099`: saved LR probability 0.565377321199892 → 0.48986648503391167, threshold 0.5, detected→missed, saved rewrite review approved. This is an illustrative prior example, not a representative new v2.1 case or proof that a specific word caused the crossing. Saved RF stays detected. Historical banking baseline has only 10 legitimate controls, with 7 LR/10 RF false positives in `results/final_detectors/metrics_by_model_and_split.csv`; those small denominators preclude broad specificity conclusions.

## Existing v2.1 pilot audit

48 legacy candidate rows / 336 condition slots, only 48 C0 texts and 288 NOT RUN generation jobs. Only 36 unique normalized source texts. No actual C1–C6 generation, review approval or detector evaluation found. These are planning artifacts, not empirical rewrite results.

## New canonical construction

441 unique safe **candidate** frames: 254 phishing-labelled, 187 legitimate-labelled; 809 duplicate excess legacy rows recorded. 22,406 within-entity near-duplicate pairs at similarity ≥0.90, not automatically treated as independent observations. 3,087 candidate condition slots: 441 C0 texts, 2,646 ungenerated C1–C6 slots. New distinct pilot selection contains 48 candidates (24/24); zero eligible for generation. 882 blank independent review assignments, zero approvals. Frozen CSV has a schema/header and **0 data rows**, manifest PENDING. No source is accepted for confirmatory evaluation merely because a canonical CSV exists.

## Confirmatory outcomes

NOT RUN. No new v2.1 probabilities, effect estimates, p-values, confidence intervals, recall shifts or prediction crossings exist. Table A describes pending candidate composition. Tables B–F have schema-only CSV/Markdown with NOT RUN status. Figures 1–5 are documented in `results/benchmark_v2_1/figures/figure_status.json`, not rendered as invented empirical figures.

## Verified engineering outputs

Six exact prompt files, inactive generator config, source registry, dedup diagnostics, structured response ingestion, objective validation, content-bound source/variant review gates, immutable freeze schema, hash-verified frozen-model evaluator, paired analysis and actual-data reporting modules exist. The offline workflow made zero API calls, zero detector predictions and zero fit calls. Final suite: 147 passed, including the non-pending freeze path using isolated test fixtures. All 360 baseline files match their saved hashes. Full details are in `ENGINEERING_REPORT.md`.
