# Presentation summary

## Phase A — Detection (historical v3)

Claim: All three models failed the sole legitimate test control.
Exact value: F1 .982456; FPR1/1.
N:29 messages,28 phishing and1 legitimate.
Evidence: preserved v3 final_run tables04/08 and FINAL_REPORT.md.
Plain-language meaning: High F1 can mask failure on the minority class.
Limitation: One negative and automated labels.
Safe wording: The selected historical test produced these decisions.
Unsafe wording: The models reliably distinguish legitimate banking SMS.

## Phase B — Generalization (historical v3)

Claim: Selected Gateway phishing recall differed.
Exact value: LR/RF167/167; separately fitted ModernBERT147/167.
N:167 phishing messages,0 legitimate.
Evidence: preserved v3 final_run table05.
Plain-language meaning: This is a conditional single-source recall observation.
Limitation: No legitimate source-test controls, no temporal experiment.
Safe wording: This selected source experiment had the reported recall.
Unsafe wording: Lexical models are universally superior.

## Phase C — AI Rewrite Robustness (new v3.2)

**PRIMARY_FAILED_COMPLETENESS_EXPLORATORY_AVAILABLE_PAIRS_COMPLETED**. Preferred100+100 and minimum30+30 not achieved. New C has {'legitimate': 1, 'phishing': 11}, complete trajectories {'phishing': 0, 'legitimate': 0}, 14 approved rewrite pairs. Prior v3 final_run is untouched.

Claim: The primary complete-trajectory experiment failed completeness.
Exact value:0 complete phishing and0 complete legitimate trajectories.
N:12 sources; 48 initial jobs; 14 approved pairs after 41 quality retries.
Evidence: frozen/matrix_manifest.json, attempts.csv, statistics/statistical_status.json.
Plain-language meaning: No source has all four approved rewrite conditions.
Limitation: One legitimate source and selective attrition; no primary inference.
Safe wording: The protocol produced selected available pairs but no complete trajectory.
Unsafe wording: A scientifically adequate expanded robustness pilot succeeded.

Claim: Available-pair threshold transitions are conditional observations.
Exact value: {"LR": 0, "ModernBERT": 0, "RF": 0} crossings by model.
N:14 available pairs per model; these repeat source frames.
Evidence: predictions/*_predictions.csv and tables/available_pair_false_positive_transitions.csv.
Plain-language meaning: Score movement can occur with or without decision changes; existing false positives are distinct from new ones.
Limitation: Available condition cohorts differ; one control cannot establish FPR.
Safe wording: On these approved pairs, the observed transitions are those saved in the paired tables.
Unsafe wording: Missing conditions establish stability or a detector’s general robustness.

Primary metrics are unavailable. Available-pair class-specific rates:

| analysis_id | hypothesis | N_frames | N_rows | model | condition | effect_size | CI | raw_p | adjusted_p | confirmatory_or_exploratory | notes | recall | false_positive_rate | specificity | false_negative_rate | accuracy | N_positive | N_negative | cohort |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| available_pair_performance | available_pair_performance | 12 | 12 | LR | C0 | 0.9166666666666666 |  |  |  | exploratory | Combined accuracy is secondary to class-separated metrics; undefined denominators are blank. | 1.0 | 1.0 | 0.0 | 0.0 | 0.9166666666666666 | 11 | 1 | available_pair |
| available_pair_performance | available_pair_performance | 2 | 2 | LR | C1 | 0.5 |  |  |  | exploratory | Combined accuracy is secondary to class-separated metrics; undefined denominators are blank. | 1.0 | 1.0 | 0.0 | 0.0 | 0.5 | 1 | 1 | available_pair |
| available_pair_performance | available_pair_performance | 5 | 5 | LR | C4 | 0.8 |  |  |  | exploratory | Combined accuracy is secondary to class-separated metrics; undefined denominators are blank. | 1.0 | 1.0 | 0.0 | 0.0 | 0.8 | 4 | 1 | available_pair |
| available_pair_performance | available_pair_performance | 4 | 4 | LR | C5 | 0.75 |  |  |  | exploratory | Combined accuracy is secondary to class-separated metrics; undefined denominators are blank. | 1.0 | 1.0 | 0.0 | 0.0 | 0.75 | 3 | 1 | available_pair |
| available_pair_performance | available_pair_performance | 3 | 3 | LR | C6 | 1.0 |  |  |  | exploratory | Combined accuracy is secondary to class-separated metrics; undefined denominators are blank. | 1.0 |  |  | 0.0 | 1.0 | 3 | 0 | available_pair |
| available_pair_performance | available_pair_performance | 12 | 12 | RF | C0 | 0.9166666666666666 |  |  |  | exploratory | Combined accuracy is secondary to class-separated metrics; undefined denominators are blank. | 1.0 | 1.0 | 0.0 | 0.0 | 0.9166666666666666 | 11 | 1 | available_pair |
| available_pair_performance | available_pair_performance | 2 | 2 | RF | C1 | 0.5 |  |  |  | exploratory | Combined accuracy is secondary to class-separated metrics; undefined denominators are blank. | 1.0 | 1.0 | 0.0 | 0.0 | 0.5 | 1 | 1 | available_pair |
| available_pair_performance | available_pair_performance | 5 | 5 | RF | C4 | 0.8 |  |  |  | exploratory | Combined accuracy is secondary to class-separated metrics; undefined denominators are blank. | 1.0 | 1.0 | 0.0 | 0.0 | 0.8 | 4 | 1 | available_pair |
| available_pair_performance | available_pair_performance | 4 | 4 | RF | C5 | 0.75 |  |  |  | exploratory | Combined accuracy is secondary to class-separated metrics; undefined denominators are blank. | 1.0 | 1.0 | 0.0 | 0.0 | 0.75 | 3 | 1 | available_pair |
| available_pair_performance | available_pair_performance | 3 | 3 | RF | C6 | 1.0 |  |  |  | exploratory | Combined accuracy is secondary to class-separated metrics; undefined denominators are blank. | 1.0 |  |  | 0.0 | 1.0 | 3 | 0 | available_pair |
| available_pair_performance | available_pair_performance | 12 | 12 | ModernBERT | C0 | 0.9166666666666666 |  |  |  | exploratory | Combined accuracy is secondary to class-separated metrics; undefined denominators are blank. | 1.0 | 1.0 | 0.0 | 0.0 | 0.9166666666666666 | 11 | 1 | available_pair |
| available_pair_performance | available_pair_performance | 2 | 2 | ModernBERT | C1 | 0.5 |  |  |  | exploratory | Combined accuracy is secondary to class-separated metrics; undefined denominators are blank. | 1.0 | 1.0 | 0.0 | 0.0 | 0.5 | 1 | 1 | available_pair |
| available_pair_performance | available_pair_performance | 5 | 5 | ModernBERT | C4 | 0.8 |  |  |  | exploratory | Combined accuracy is secondary to class-separated metrics; undefined denominators are blank. | 1.0 | 1.0 | 0.0 | 0.0 | 0.8 | 4 | 1 | available_pair |
| available_pair_performance | available_pair_performance | 4 | 4 | ModernBERT | C5 | 0.75 |  |  |  | exploratory | Combined accuracy is secondary to class-separated metrics; undefined denominators are blank. | 1.0 | 1.0 | 0.0 | 0.0 | 0.75 | 3 | 1 | available_pair |
| available_pair_performance | available_pair_performance | 3 | 3 | ModernBERT | C6 | 1.0 |  |  |  | exploratory | Combined accuracy is secondary to class-separated metrics; undefined denominators are blank. | 1.0 |  |  | 0.0 | 1.0 | 3 | 0 | available_pair |


Every table value has a coordinate in RESULT_EVIDENCE_INDEX.csv. See PRESENTATION_GRAPH_NOTES.md for figure explanations.
