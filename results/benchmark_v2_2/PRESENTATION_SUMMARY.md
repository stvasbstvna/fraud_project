# V2.2 presentation summary

**Status: V2.2 SOURCE COHORT INSUFFICIENT.** This run performed deterministic source feasibility checks only. No independent human annotation, fresh LLM semantic review, generation or detector scoring occurred. The planned machine semantic review would not replace independent human annotation.

## Source audit

Claim: The audit expanded source discovery and inspected original/local inputs.

Exact number: 81,738 input rows, including repeated/historical data; 23,731 broad financial/known-institution candidates.

Evidence: `source_summary.json`, `source_audit_counts.csv`, `data/benchmark_v2_2/source/source_registry.json`.

Plain-language meaning: We searched widely, but a search hit is not automatically a genuine bank message.

Limitation: This is a scoped keyword/institution screen, not a census of all banking SMS. Most preliminary positive candidates were not fully family/contamination screened after the control gate failed.

## Apparent source diversity

Claim: Many controls appearing in two datasets were actually the same messages.

Exact number: Of 50 rule-clear Mendeley ham rows, 43 have original-message SHA-256 identical to UCI. The two files together contain 100 rule-clear ham rows across 49 candidate families.

Evidence: `tables/Audit_control_lineage.csv` and row-level `source_lineage_basis` in `data/benchmark_v2_2/source/candidate_audit.csv`.

Plain-language meaning: Copying a message into a second dataset does not create a second independent source.

Limitation: The seven unmatched Mendeley families are only potentially independent; their bank authenticity remains unreviewed.

## Why execution stopped

Claim: The screened pool cannot satisfy the minimum control cohort with the declared source limits.

Exact number: At most seven non-UCI control families; source cap 50% implies at most 7+7 = **14** controls, below required **16**. Final accepted source frames: **0**.

Evidence: `tables/Audit_capacity.csv`, `source_summary.json`, `data/benchmark_v2_2/frozen/source_cohort_manifest.json`.

Plain-language meaning: Even assuming every candidate passes later review, too few independent controls remain. We stopped before producing rewrites or scores.

Limitation: Fourteen is an optimistic upper bound, not a validated cohort. Further sources or resolved provenance could change a future run.

## Newly discovered financial collection

Claim: More messages alone do not resolve source validity.

Exact number: New licensed corpus 523 rows; 213 broad financial candidates include 64 ham. Zero admitted because row-level SMS/chat/email channel is absent.

Evidence: `data/benchmark_v2_2/source/source_registry.json`, `source_audit_counts.csv`, `docs/benchmark_v2_2/DATA_PROVENANCE.md`.

Plain-language meaning: We cannot silently call every short message an SMS when its source mixes communication channels.

Limitation: These are held candidates, not demonstrated invalid messages. Row-level provenance could support future reconsideration.

## Detector results and software verification

Claim: No v2.2 detector effect was measured; historical evidence was preserved.

Exact number: Zero generated variants, predictions and scientific figures. Twelve result schemas are NOT RUN; two supplementary tables contain actual source-audit findings. The historical verifier checks 979 files with zero changes and unchanged LR/RF hashes.

Evidence: `verification.json`, `tables/table_status.csv`, `figures/figure_status.json`, `docs/benchmark_v2_2/TEST_RESULTS.md`.

Plain-language meaning: The result is an identified data shortage, not a conclusion that a detector succeeded or failed.

Limitation: Tests prove the implemented checks, not real-message truth, valid prompts or a completed experiment.

## What to say on each figure

No scientific figures were generated because no accepted cohort or frozen predictions exist. The following are prospective axes, not observed results. No points or lines exist in this run.

| Figure | X-axis if run | Y-axis if run | What each point/line would mean | Main takeaway now | What not to conclude |
|---|---|---|---|---|---|
| 1 | C0/C1/C4/C5/C6 | Phishing recall | Detector recall on the same complete source cases | NOT AVAILABLE | No measured recall stability/drop |
| 2 | Core condition | Paired probability change | Source-paired scores with frame-level summaries | NOT AVAILABLE | No largest condition effect |
| 3 | Surface distance | Absolute probability movement | Approved source/condition pair, repeated within frame | NOT AVAILABLE | No distance association or causality |
| 4 | Condition | Threshold-transition count | Paired class changes by detector | NOT AVAILABLE | Zero predictions do not imply zero crossings |
| 5 | Condition | Legitimate false-positive behavior | Already/new/recovered false alarms on controls | NOT AVAILABLE | No real-world FPR estimate |
| 6 | Core condition | Probability on a representative complete trajectory | Frame nearest median average movement, ID tie-break | NOT AVAILABLE | No extreme example relabeled representative |
| 7, optional | Condition with source strata | Performance or score movement | Descriptive source-specific repeated observations | NOT AVAILABLE | No evidence of cross-source consistency |

Safe presentation sentence: “Our v2.2 source audit found that dataset overlap inflated the apparent number of independent controls. The strongest possible cohort under our source limits had fewer than the required controls, so we stopped before generation and detector evaluation.”

Scale to full benchmark: **NO**, pending sufficient supported banking controls and a successful prospective prompt pilot.
