# Symposium evidence summary — pilot checkpoint 2026-11-06

**Current status: PILOT NOT READY.** No v2.1 detector result is available. The completed work is source auditing, template-controlled candidate selection and review preparation.

## Research question and mechanism

Which linguistic changes are associated with changes in detector behavior when intent and requested action stay fixed?

Original safe SMS → exact C1–C6 rewrite prompt → saved rewrite → independent semantic review → frozen detector → paired probability and decision comparison.

C0 is the original safe baseline. C1 changes a few words; C2 makes the same action direct; C3 expresses it indirectly; C4 normalizes grammar/fluency; C5 strongly paraphrases; C6 seeks high surface change while preserving meaning. These transformations are planned; they have not yet been generated for this pilot.

## Evidence-backed claims

| Claim | Exact number | Evidence file | Plain-language explanation | Limitation |
|---|---|---|---|---|
| Three original sources were row-audited | Mendeley 5,971; Gateway 68,029; UCI 5,574 | `diagnostics/pilot_original_source_audit.json` | Original data were inspected and their snapshots hashed; the Mendeley archive matches its publisher hash. | These totals include overlapping/nonfinancial messages and are not the research sample. |
| A safer candidate queue was selected | 29 candidates: 24 phishing-labelled, 5 legitimate-labelled | `data/benchmark_v2_1/source/pilot_48_candidates.csv`; `diagnostics/pilot_selection_summary.json` | Proposed examples are ready for people to inspect. | Labels remain unvalidated; the name pilot_48 describes the target, not achieved N. |
| Template redundancy was controlled prospectively | 29 selected families; 0 selected near-duplicate matches under the defined rule | `diagnostics/pilot_template_families.csv` | Differences limited to banks, amounts or placeholders do not automatically count as independent messages. | Family detection is heuristic and requires human review. |
| Training overlap was screened | 71 candidate exclusions | `diagnostics/pilot_training_overlap.csv` | Text/template matches to train or validation were excluded before any detector scoring. | This does not prove that every possible upstream or paraphrase overlap was removed. |
| The target remains incomplete | At least 19 further independent control candidates needed | `diagnostics/pilot_selection_summary.json` | There are not yet 24 credible, reviewed banking controls. | Existing five proposed controls may also fail review; Gateway is 17/29 of the reduced queue, so source balance remains unresolved. |
| Scientific collection has not started | 0 source-approved frames; 0 rewrites; 0 complete-case frames; 0 final condition rows | `diagnostics/pilot_generation_readiness.json` | No unreviewed source was sent to generation and no result was invented. | 58 blank Stage A assignments are preparation, not completed human review. |

Paths beginning `diagnostics/` refer to `results/benchmark_v2_1/diagnostics/`.

## Models

The existing TF-IDF + Logistic Regression and TF-IDF + Random Forest pipelines remain frozen, with verified historical hashes, 3,715 fitted vocabulary entries each and a fixed 0.5 decision threshold. They were not retrained or used to score this candidate selection. Exact model evidence remains in `docs/benchmark_v2_1/FROZEN_MODEL_CARD.md` and the earlier runtime audit.

## Prior v1 result — historical context only

| Claim | Exact number | Evidence file | Plain-language explanation | Limitation |
|---|---|---|---|---|
| Prior neutral rewriting showed a small observed net recall difference | 143 phishing pairs; LR 98.6014%→97.9021%; RF 97.9021%→97.2028%; exact McNemar p=1.0 each | `results/rewrite_experiment/statistical_tests.csv` | Each model had one net additional miss in the saved earlier experiment. | This does not establish systematic deterioration and is not C0–C6 pilot evidence. |
| Prior UNIONBANK illustration crossed the LR threshold | 0.5653773212→0.4898664850 at 0.5; detected→missed | `results/rewrite_experiment/paired_predictions.csv`, BRW-0099 | One saved prior message changed a detector decision after rewriting. | It is not representative of the new pilot, not assigned to C1–C6, and does not identify a causal word. |

Do not pool these values numerically with v2.1.

## Planned graphs — no empirical pilot figures yet

| Graph | X-axis | Y-axis | Points/lines | Audience should notice | What NOT to conclude |
|---|---|---|---|---|---|
| 1. Recall across conditions | C0–C6 | Recall, 0–1 | Separate LR/RF lines | Whether reviewed transformations change detection rates | No direction or condition effect is known yet. |
| 2. Paired score change | C1–C6 | P(C0)−P(Ci) | Means/medians and frame-bootstrap uncertainty by model | Positive values would mean lower rewrite scores; uncertainty matters | A lower probability is not automatically a missed phishing message or a general vulnerability. |
| 3. Distance versus movement | Prespecified surface distance | Signed or absolute paired score movement | Each actual variant as a point; LR and RF shown separately | Whether larger text changes accompany larger score movement | Correlation does not prove that a wording feature caused an error. |
| 4. Decision transitions | Condition | Four transition directions | Counts, separately by model | Both new errors and recoveries, including legitimate false positives | Do not report only detected→missed changes. |
| 5. Representative trajectory | C0–C6 | Phishing probability, 0–1 | LR/RF lines, threshold 0.5 | How the same reviewed message moves across conditions | Do not choose the largest change as the representative. Select nearest median frame-mean absolute movement, with deterministic ties. |

Figure status: `results/benchmark_v2_1/figures/pilot_48_figure_status.json`. Table A reports pending candidate composition; scientific Tables B–F and the qualitative example are schema-only/NOT RUN. No representative rewritten message or legitimate false-positive example exists for this pilot yet.

## Next research step

Two independent reviewers must complete Stage A in `data/benchmark_v2_1/review/pilot_source_review.csv`, validate/correct labels and action eligibility from source evidence, and review template independence. Add sufficient licensed independent banking controls, or approve a prospective reduced-design amendment addressing imbalance. Only then proceed through generation, separate Stage B semantic review, manipulation checks, immutable freeze, fixed-detector evaluation and frame-paired analysis.

Do not claim a validated 48-frame/336-row pilot, new detector performance, successful evasion, significant condition effects, lexical causality or completed human review. Recommendation: **do not scale beyond the pilot yet**.