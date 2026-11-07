# Pilot execution report — 2026-11-06

**PILOT NOT READY.** Execution reached the genuine Stage A human-review boundary. No generation, rewrite approval, scientific freeze, detector evaluation or inferential analysis was fabricated beyond it. This report is the current pilot checkpoint; older ENGINEERING_REPORT/RESULTS files remain preserved historical checkpoints.

## 1. Initial candidates

The master pool remains 441 unique unvalidated synthetic texts (254 phishing-labelled/187 legitimate-labelled). This run audited original Mendeley 5,971 rows, Gateway 68,029 rows and UCI 5,574 rows: 79,574 original records in total, not independent unique messages. Financial screening retained 1,287 safe audit rows (63 Mendeley, 1,197 Gateway, 27 UCI). Combined with master candidates, the diagnostic pool contains 1,728 rows. Sources overlap; totals must not be reported as independent research sample size.

## 2–3. Reviewed, accepted and rejected source frames

Human-reviewed sources: **0**. Human-approved: **0**. Human-rejected: **0**. Selected pending review candidates: **29**. 58 Stage A assignments (two per source) are in `data/benchmark_v2_1/review/pilot_source_review.csv`. Algorithmic filtering is not human review or source approval. `true_label`, intent/action/destination annotations stay blank pending actual reviewers.

Seventy-one otherwise-selectable candidates matched a train/validation template witness and were excluded by the prospective screen. Other exclusions include spam/unknown labels, personal chat/telecom top-ups unsuitable as bank-notification controls, language/length screens and damaged source encoding. Exact per-row reasons remain in `source/pilot_audited_candidate_pool.csv`; overlap witnesses are in `diagnostics/pilot_training_overlap.csv`.

## 4. Template families

`pilot-template-v2` uses placeholder/entity/number/legacy-event normalization plus token Jaccard and structural similarity, followed by connected components. The joint pool has 268 detected families; the 441 legacy candidates occupy only 8 of those joint-pool families. Twenty-nine selected candidates occupy 29 families, with zero selected pairwise near-duplicate matches **under this rule**. This is heuristic evidence, not independent human verification of all template/campaign relationships. Method and exact thresholds: `PILOT_SELECTION_METHOD.md`. Required per-frame diagnostics: `results/benchmark_v2_1/diagnostics/pilot_template_families.csv`.

## 5. Current composition, not a final validated pilot

| Source | Pending candidates |
|---|---:|
| SMS Gateway, original pinned release | 17 |
| Mendeley v1, original publisher-hash-verified archive | 8 |
| Preserved synthetic legacy controls | 3 |
| UCI original archive | 1 |
| **Total** | **29** |

Candidate labels: **24 phishing-labelled / 5 legitimate-labelled**. All remain unvalidated. Target 48/24+24 is not met; at least 19 additional independent legitimate-control candidates are needed if all five survive review, potentially more if they fail. Gateway contributes 17/29=58.62% of this reduced queue; source balance and synthetic-control/label confounding remain explicit blockers. Do not call this a clean balanced 48-frame pilot. File `source/pilot_48_candidates.csv` preserves the requested target-oriented name but contains exactly 29 candidate rows.

## 6. Exact prompts

Existing `canonical-v1` C1–C6 prompt files and generator config are unchanged. No v2 prompt was created: the immediate blocker is source validity/selection, not evidence of failed prompt manipulation. No prompt was executed. Source registry and prompt/config/model files retain their pre-run hashes.

## 7–8. Generation and failures

Generated rewrites: **0**; API generation calls: **0**; technical generation failures: **0 (NOT ATTEMPTED)**. Do not call this a successful zero-failure generation run. Config remains `active=false`, inherited model availability unverified. Credentials were not inspected because missing C0 approval already prohibits generation. The model was not substituted or queried. Requested maximum 288 generations/336 complete condition rows is a target only.

## 9. Human-review results

Stage A has 58 blank independent assignments, zero approvals and 29 unresolved frames. Checks distinguish source/label/provenance, English/channel, banking relevance, intent/action/entity/destination, safety and family validity. Reviewers must agree on controlled semantic annotations, not merely tick a shared approval box. Decisions bind source metadata/text/family evidence by SHA-256.

Stage B rewrite review is separate: `review/pilot_rewrite_review.csv` is a schema with **0 rows**, because no rewrite exists. It contains same-intent/action/entity/destination/label, no-new-facts, condition compliance, naturalness and safety fields. No source decision is relabeled as rewrite preservation approval. Agreement/adjudication statistics are NOT AVAILABLE.

## 10. Completeness and attrition

Starting target: 48 frames; selected source-review queue: 29; source-approved: 0; generated C1–C6: 0; rejected generated variants: 0 (none attempted); complete-case frames: 0; final approved condition rows: 0. Every candidate currently has `pilot_complete_case=false`. Condition-level generation/review attrition is NOT AVAILABLE, not zero experimental attrition. The original 441-frame pool and all earlier pilots stay unchanged.

## 11. Manipulation check

NOT RUN. No C1–C6 observations exist, so there is no evidence that C1 is closer than C5/C6 or that C3 differs in directness. No ordering was forced. Template similarity is a source-selection diagnostic and must not be presented as a rewrite-distance manipulation result.

## 12–16. LR/RF performance, score movement, transitions, false positives and statistics

All **NOT RUN** for this pilot. Existing frozen detectors were neither retrained nor used to score candidate selection. No recall/FNR/FPR, probability deltas, threshold crossings, bootstrap intervals, p-values or new false-positive examples are available. The prewritten frame-aware/Holm plan remains unchanged; no test was selected from outcomes.

Table A at `results/benchmark_v2_1/tables/pilot_48/A_pilot_composition.csv/.md` reports actual **candidate** source/label/category/entity/family composition. B–F and the qualitative prompt-example table have headers only and explicit NOT RUN status. Five scientific figures were not rendered with invented data; `results/benchmark_v2_1/figures/pilot_48_figure_status.json` records axes, planned marks and interpretation limits. No representative frame is selected before approved outputs and full analysis.

## 17. Limitations and execution findings

Main blockers: missing independent source reviews, at least 19 missing independent banking control candidates, source/label imbalance, inactive provider execution and absent rewrite reviews. Some original smishing labels appear ambiguous on reading; source metadata alone cannot establish malicious intent. Entity extraction is provisional, and regex defanging can over-mask dates/numbers; Stage A must flag/correct semantic distortion through a versioned source artifact, not edit old C0 silently. Notification-only controls may lack a genuine action for C2/C3: reviewers must resolve eligibility rather than invent an action.

Language/banking/near-duplicate screens are fallible. Training template matching cannot prove absence of all contamination. Synthetic controls affect external validity. A reduced N requires a prospective protocol amendment and actual reviewed data; source approvals alone do not authorize a smaller/single-class cohort.

Gateway's six-name header/seven-value rows caused a current-run draft parser error; corrected and regression-tested before final selection. Superseded current-run artifacts remain archived, not silently reinterpreted. Independent code review found a cohort gate that could authorize a reduced/single-class set after source review; fixed to enforce 48, agreed 24/24 labels, unique validated families, selection eligibility, source and entity balance. Nearest compatible witness selection was corrected to scan all references with deterministic ties.

## 18–19. Presentation boundaries

Safe now: verified source-access/audit counts, template-screening diagnostics with method caveats, the 29-candidate/24+5 shortage and honest PILOT NOT READY status, plus explicitly historical v1 observations. Do not present proposed labels as truth or any new detector/rewrite effect.

Prior v1 result only: LR recall 98.6014%→97.9021%; RF 97.9021%→97.2028%; 143 phishing pairs; exact McNemar p=1.0 for each. UNIONBANK LR 0.5653773212→0.4898664850 at threshold .5 is an old illustrative crossing, not C1–C6 evidence or a new representative trajectory. Numerical v1/v2.1 pooling is prohibited.

## 20. Scale recommendation and exact next action

**Do not scale beyond the pilot. Do not generate from the current queue yet.** Two independent human reviewers must complete `review/pilot_source_review.csv`, using original-source evidence and `PILOT_SELECTION_METHOD.md`, adjudicate source labels/action eligibility/families, and obtain at least 19 more suitable controls (or an explicit prospective reduced-design amendment addressing source imbalance). If annotations require source-text changes, create a new version and new content-bound reviews.

Read-only readiness command after genuine reviewer work:

```powershell
.\.venv\Scripts\python.exe -m src.benchmark_v2_1.pilot_review --reviews data/benchmark_v2_1/review/pilot_source_review.csv
```

It currently returns `PILOT NOT READY`, 29 candidates, 0 approved, `generation_allowed=false`. Filling a CSV cannot waive missing target/cohort requirements. Formal import to the existing canonical generation schema and all downstream stages remain after the external review boundary; no old semantic-review checkbox is manufactured automatically to make the new Stage A form pass.

Reproduction from a clean output namespace: `pilot_sources` → `pilot_selection` → `pilot_review` → `pilot_status_report` (all `python -m src.benchmark_v2_1.<module>`). Materialization commands refuse occupied paths. Review/protocol details and exact retrieval hashes are in `PILOT_SELECTION_METHOD.md`.

## Verification and preservation

Full suite: **159 passed in 9.38s**, command ` .\.venv\Scripts\python.exe -m pytest -q --basetemp .pytest_cache/pilot-final-suite-20261106`. New parser/family/cohort tests were observed failing before fixes. No failing tests remain; that does not make the scientific pilot valid. Final preservation verification checked 440 pre-run files: **439 unchanged**, with only the user-requested presentation summary updated. Its archive `PRESENTATION_SUMMARY_before_pilot.md` matches the original SHA-256 exactly. All prior code/config/prompts/model/data/other-result files remain unchanged. Evidence: `results/benchmark_v2_1/diagnostics/pilot_preservation_verification.json`. It also independently checks 29 unique selected families, blank true labels, 58 pending source-review assignments and blocked generation; zero texts triggered the automated endpoint screen, which is not a substitute for human safety approval.
