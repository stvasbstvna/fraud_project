# Automated pilot: presentation evidence

**The pilot used automated semantic review rather than independent human annotation.** Reviews used separate contexts and two model snapshots; shared provider/model biases remain possible. All results below concern the separate exploratory available-pair analysis. The primary complete-case pilot failed completeness.

## Source sample

Claim: A small balanced cohort survived source review.

Exact number: Four sources, two phishing and two legitimate, four template families; 29 source cases reviewed, 19 approved before balance.

Evidence: `automated_pilot/tables/Table1_cohort_composition.csv`, `automated_pilot/source_summary.json`.

Plain-English explanation: We found only two acceptable distinct control cases, so we matched them with two phishing cases.

Limitation: Both controls are synthetic and both phishing cases come from Mendeley. Source and label are perfectly confounded.

## Generation and completeness

Claim: Real generation ran, but the full experiment did not pass its own completeness requirements.

Exact number: 24 generated variants, 16 approved, eight rejected; zero complete C0–C6 cases, zero primary frozen rows. Separate exploratory freeze: 20 rows, including four originals.

Evidence: `automated_pilot/tables/Table2_automated_review_outcomes.csv`, `automated_pilot/condition_attrition.csv`, primary and exploratory freeze manifests.

Plain-English explanation: Several rewrites repeated their original exactly. We kept the rejection rules and analyzed only explicitly approved pairs separately.

Limitation: Missing conditions and selective survival prevent a fair complete ranking of linguistic conditions. C2 has no approved variants.

## Detector decisions

Claim: Accepted rewrites changed no predicted classes in this sample.

Exact number: Zero crossings in 16 pairs for LR and zero in 16 for RF. Both classified all 20 available rows as phishing.

Evidence: `automated_pilot/tables/Table4_detector_performance.csv`, `Table6_decision_transitions.csv`, verified predictions.

Plain-English explanation: Scores moved, but every observed score stayed on the same side of the decision boundary.

Limitation: Four source messages cannot demonstrate general detector stability. Phishing recall at C1/C2 is unavailable, not zero or proven unchanged.

## Largest observed score movement

Claim: A large probability movement can occur without a changed decision.

Exact number: MetroTrust legitimate RF C5, tied C6: 0.5623924 → 0.7133971, an increase of 15.1005 percentage points; prediction 1→1.

Evidence: `automated_pilot/tables/Table7_largest_absolute_movements.csv`, `automated_pilot/extreme_cases.csv`.

Plain-English explanation: The detector became more confident in its existing false alarm.

Limitation: This was selected as the largest observed extreme. It is not representative, and no complete approved prompt trajectory exists.

## False positives

Claim: The synthetic controls were already false alarms before rewriting.

Exact number: Two of two legitimate C0 sources and nine of nine accepted legitimate variants flagged by each detector.

Evidence: `automated_pilot/tables/Table8_legitimate_false_positives.csv`.

Plain-English explanation: Rewriting did not create these false alarms; the original messages were already flagged.

Limitation: Nine rewrites are repeated observations from only two synthetic messages. This is not an estimate of real bank-message false-positive rates.

## Distance and statistical evidence

Claim: The available observations do not establish a general relationship between linguistic distance and score movement.

Exact number: Mean within-frame absolute-movement slopes on two phishing sources: LR −0.0415904; RF +0.0790463. Zero primary Holm tests were run; all seven planned primary entries are NOT RUN.

Evidence: `automated_pilot/distance_associations.csv`, `automated_pilot/primary_holm_family_NOT_RUN.csv`.

Plain-English explanation: The two detectors show different descriptive patterns, and there are too few independent messages for a reliable general conclusion.

Limitation: Tiny sample, missing conditions, review selection and shared source effects. Bootstrap intervals are descriptive, even when they exclude zero.

## What to say on each graph

### Figure 1 — recall on available pairs

File: `automated_pilot/figures/Figure1_recall_available_pairs.png` (also SVG).

X-axis identifies condition C0–C6. Y-axis is phishing recall among the available phishing source messages. Each detector series summarizes its surviving cases; gaps mean no eligible phishing observation. Say: “All observed phishing cases were detected.” Do not say missing conditions had zero recall, that the sample is complete, or that recall is generally robust.

### Figure 2 — probability changes

File: `automated_pilot/figures/Figure2_probability_change_available_pairs.png` (also SVG).

X-axis identifies rewrite condition. Y-axis is original phishing probability minus rewritten probability: positive means a lower rewritten score. Separate panels distinguish phishing and legitimate sources. Points/lines summarize paired changes for each detector, with descriptive frame-bootstrap intervals. Say: “Scores move in both directions while observed decisions remain unchanged.” Do not interpret the connecting line as an equal-spaced dose response, or the tiny-sample intervals as confirmatory significance.

### Figure 3 — distance versus movement

File: `automated_pilot/figures/Figure3_distance_movement_available_pairs.png` (also SVG).

X-axis is distance measured using the frozen fitted TF-IDF representation. Y-axis is absolute change in phishing probability. Each point is an accepted source/condition pair; panels separate LR and RF. Say: “These are repeated observations from very few source messages.” Do not treat points as independent samples or claim that distance causes detector failure.

### Figure 4 — decision transitions

File: `automated_pilot/figures/Figure4_transition_counts_available_pairs.png` (also SVG).

X-axis identifies conditions; Y-axis counts paired threshold transitions by detector/transition category. Zero counts apply only to observed pairs; unavailable categories remain gaps. Say: “None of the approved pairs crossed the fixed 0.5 threshold.” Do not count rejected or missing rewrites as stable predictions.

### Unavailable figures and examples

Figure 5 and a representative complete prompt trajectory are NOT AVAILABLE because no frame has all approved conditions. `automated_pilot/prompt_trajectory_NOT_AVAILABLE.csv` is explicitly empty. Optional Figure 6 was omitted because the sample is too small. The ranked extreme example must never be relabeled representative.

## Verification and safe symposium statement

Eight tables and four scientific figures were generated. The repository suite passed 172 tests; verification found zero changes among 489 pre-existing files. Evidence: `automated_pilot/verification.json` and `docs/benchmark_v2_1/AUTOMATED_PILOT_FINAL_REPORT.md`.

Safe statement: “In a four-source, automatically reviewed diagnostic sample, approved rewrites moved TF-IDF detector scores without changing decisions. The full condition protocol yielded no complete cases, so the planned confirmatory experiment remains unavailable.”
