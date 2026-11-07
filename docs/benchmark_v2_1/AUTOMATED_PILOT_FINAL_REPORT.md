# Automated pilot final report — 2026-11-06

Status: **PRIMARY_PILOT_FAILED_COMPLETENESS_EXPLORATORY_RESULTS_AVAILABLE**.

**The pilot used automated semantic review rather than independent human annotation.** Separate model contexts do not establish statistical independence, expert judgment, or independent source truth. This is a research limitation.

## Sample and source selection (items 1–4)

The expanded local audit inspected 1,743 candidates, including 15 additional financial ham candidates from SmishX that remained on HOLD for unresolved rights/provenance. Deterministic screening rejected 485 candidates. Eligible distinct families numbered five legitimate and 205 phishing candidates. Twenty-nine source cases received actual machine review: all five control families and 24 phishing candidates. Nineteen were approved before balancing (17 phishing, two legitimate). The largest balanced cohort under the declared source-capacity constraints contains **four source frames: two phishing and two legitimate, four template families**. No source supplies more than half the cohort.

Both phishing frames are from Mendeley; both legitimate controls are legacy fictional SYNTH-V21 banking messages. Thus source and label are perfectly confounded. This is not a representative real banking control sample. The original target of 48 sources was not achieved. Training/validation overlap screening and family-level exclusion preceded selection; this does not prove absence of every historical or pretraining overlap.

Evidence: `data/benchmark_v2_1/source/automated_audited_pool.csv`, `automated_source_cohort.csv`, and `results/benchmark_v2_1/automated_pilot/source_summary.json`.

## Automated methodology (items 5–7)

The additive CLI requires `--review-mode automated`; the old human review forms and workflow remain unchanged. The protocol fixed confidence at 0.80, exact role snapshots, isolated A/B contexts, deterministic source checks, source limits, family controls, and no semantic regeneration. Review payloads exclude detector predictions. Source decisions bind exact text, metadata and hashes; rewrite decisions bind exact source, condition, prompt, generated text and actual raw provider responses. Freeze and cached evaluation reconstruct approvals and verify artifact/model hashes before accepting results.

| Role | Exact snapshot | Actual research calls |
|---|---|---:|
| Generator | gpt-5.4-mini-2026-03-17 | 24 |
| Reviewer A | gpt-5.4-mini-2026-03-17 | 45 |
| Reviewer B | gpt-4.1-mini-2025-04-14 | 45 |
| Adjudicator | gpt-4.1-2025-04-14 | 21 |

There were 135 completed research calls, zero technical failed call records, 79,785 input tokens and 13,879 output tokens. One neutral capability probe and three model-metadata GET requests are separate from research calls. No model substitution occurred. A and the generator share a snapshot; all roles share a provider and may share biases.

Source A/B label agreement was **25/29 (86.21%)**. Twenty-one source adjudications also addressed semantic-field differences; they are not 21 label disagreements. Ten source cases were rejected. The 16 rewrites reaching semantic review had matching critical A/B decisions, all approved; there were zero rewrite adjudications. Agreement after deterministic selection is not an unbiased estimate of review accuracy.

## Generation, attrition and manipulation (items 8–12)

Existing C1–C6 generation prompts were preserved. Four sources produced 24 real variants, one response per condition, with zero technical generation failures and no retries to obtain semantic acceptance. Eight variants were rejected (33.33%): seven exact copies and one literal entity-span mismatch. Sixteen passed deterministic checks and both semantic reviewers.

| Condition | Generated | Approved | Rejected |
|---|---:|---:|---:|
| C1 | 4 | 1 | 3 |
| C2 | 4 | 0 | 4 |
| C3 | 4 | 4 | 0 |
| C4 | 4 | 4 | 0 |
| C5 | 4 | 4 | 0 |
| C6 | 4 | 3 | 1 |

All four C2 outputs copied already direct source text and failed the unchanged-text rule. The C6 mismatch changed “transaction for AUD 788.93” to “transaction of AUD 788.93”; the source reviewer had selected that broad phrase as the entity. This is a possible annotation/rule artifact, not proof of a changed bank identity. Rules were not relaxed after observing attrition or scores.

**Complete-case N = 0; primary frozen rows = 0.** `automated_pilot_frozen.csv` contains headers only; its manifest says `NOT_FROZEN_NO_COMPLETE_CASES`. The complete-case primary analysis, seven-test Holm family and representative C0–C6 trajectory are NOT RUN/NOT AVAILABLE. No complete trajectory was fabricated.

A separate available-pair analysis plan was saved before first scoring. Its explicitly exploratory freeze contains four C0 anchors plus 16 approved variants: **20 rows from four sources**, with C0–C6 counts 4, 1, 0, 4, 4, 4, 3. The partial matrix fails the primary complete-case validator. It is stored as `automated_available_pairs_exploratory.csv` with a separate manifest and predictions file.

Manipulation checks cannot validate the complete condition sequence. C1/C5 and C1/C6 distance-order comparisons each have one paired legitimate frame and fraction 1.0; C2/C3 has zero pairs. These do not establish a valid population-level dose ordering. Numeric condition indices are not treated as equal-spaced linguistic doses.

## Frozen detector observations (items 13–17)

Actual saved LR and RF pipelines were used without fitting or tuning, threshold 0.5. Their model hashes remain:

* LR: `84ba84863ce9a8fd757cd4e9babc6dacf39496223299a06df0054f94ca688fcc`
* RF: `99c4a06e7ad52ff000c0a1d8818ca61cdc268d929a1a970e79d74b6e0c38b4fc`

Both models classify all 20 available rows as phishing. Each detects both phishing anchors and all seven accepted phishing variants. Each already flags both synthetic legitimate anchors and all nine accepted legitimate variants. There are **zero threshold crossings among 16 approved source/variant pairs per model**. The repeated variants are not independent new controls.

Recall is 1.0 at observed phishing conditions C0, C3, C4, C5 (two sources each) and C6 (one source); C1/C2 phishing recall is undefined. Observed legitimate FPR is 1.0 wherever controls exist; C2 is undefined. This is not a real-world banking FPR estimate. On the common four-frame C0/C3/C4/C5 subset, accuracy is 0.5, precision 0.5 and F1 2/3 for both detectors. C6 accuracy 1/3 reflects a different class mixture, not changed decisions.

Probability movement uses delta = P(C0) − P(Ci). The largest observed absolute movement is the MetroTrust legitimate RF C5 case, tied with C6: **0.5623924014023075 → 0.7133970802613095**, delta −0.151004678859002 (increase 15.1005 percentage points), prediction 1→1. It is an explicitly ranked extreme, not a representative example. LR's largest absolute movement is also MetroTrust C5/C6, approximately 0.0891. No all-condition ranking is valid with C2 missing and unequal surviving pairs.

## Statistics (item 18)

Eight tables and four PNG/SVG figures were generated from verified predictions. The primary seven-test Holm family has no p-values because no complete cases exist. Available-pair summaries and frame bootstrap intervals are descriptive only. Among two phishing source frames, the mean within-frame slope of absolute movement against frozen-vectorizer distance is LR −0.0415904, RF +0.0790463. Corresponding 95% frame-bootstrap intervals are [−0.142990, 0.059809] and [0.061803, 0.096290]. With two frames, selection and missing conditions, even an interval excluding zero does not support a confirmatory or generalizable association. Mean within-frame LR/RF signed movement correlation across four sources is 0.6440403, also descriptive.

## Direct answers to research questions

1. **Largest condition change:** the largest individual observed absolute movement is RF C5, tied C6, on one legitimate MetroTrust source. The design cannot determine a general largest C0–C6 effect.
2. **Distance versus movement:** descriptive slopes differ between LR and RF on two phishing frames; greater distance is not established as a general cause or predictor of larger movement.
3. **Recall reduction:** none observed in accepted pairs. The tiny, incomplete sample cannot establish recall stability generally.
4. **Threshold crossings:** all observed conditions have zero crossings for both detectors; missing conditions are not evidence of zero effect.
5. **Controls:** both synthetic controls are false positives already at C0. Scores vary without changing their predicted class. Real legitimate banking behavior remains unresolved.
6. **LR versus RF:** decisions coincide throughout; probability movements differ in magnitude. Their descriptive within-frame movement correlation is 0.6440, not proof of equivalent response.
7. **TF-IDF stability:** these observed rewrites move scores without crossing the fixed threshold. This supports a narrow observation about these saved pipelines and selected messages, not broad robustness or vulnerability claims.

## Conclusions, limitations and recommendation (items 19–22)

The strongest supported conclusion is that real, automatically screened rewrites can move detector probabilities while preserving decisions in this four-source diagnostic sample. Equally important, the existing condition protocol did not produce a single complete approved trajectory. Do not claim a completed 48-source pilot, 336 frozen rows, human/expert annotation, linguistic causality, significant primary effects, representative examples, real-world FPR, or generalized detector robustness/vulnerability.

Limitations include four source frames, two synthetic controls, perfect source/label confounding, source-label uncertainty, shared provider biases, incomplete conditions, selective attrition, missing C2, and tiny bootstrap support. Defanging masked date fragments as phone placeholders in phishing texts; the overly broad entity annotation can trigger false deterministic rejection. Existing C1 prompts produced minimal-change failures, and already-direct C2 sources produce exact copies. These are design findings, not grounds for silently changing this run.

Do not scale this protocol unchanged. A future version should acquire independently supported real banking controls, fix typed entity and date-aware defanging rules, predefine treatment of already-direct C2 anchors, strengthen measurable C1 manipulation, and prospectively pilot condition validity and family dependence. Preserve this run and preregister changes before a fresh run; do not regenerate until desired significance or completeness appears.

## Verification, evidence and reproduction

Final repository suite: **172 passed in 15.51s**. Independent code review found evidence-binding and cached-prediction integrity gaps; both were corrected with regression tests. The final verifier checks raw provider evidence, roles, approvals, frozen/prediction/model hashes, paired deltas and table counts. All 489 pre-existing inventory files are unchanged. No human forms, historical results or fitted models were altered; no commit or push occurred.

```powershell
.\.venv\Scripts\python.exe -m src.benchmark_v2_1.automated_pilot --review-mode automated --stage all --offline
.\.venv\Scripts\python.exe -m pytest -q --basetemp .pytest_cache/automated-final-suite-20261106b
```

Offline replay requires existing caches and makes no API calls. Actual requests/raw responses are retained under `data/benchmark_v2_1/generated/automated_pilot/calls/`. Review artifacts are in `data/benchmark_v2_1/review/automated_*.csv`; tables, figures, attrition, primary NOT RUN tests and `verification.json` are under `results/benchmark_v2_1/automated_pilot/`. The exploratory prediction SHA-256 is `704735d8760bd0452b62bbca08553990114d3c83fe056d83342ed055d792b23f`.
