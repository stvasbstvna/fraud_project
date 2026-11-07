# Benchmark v3.2 final report

**PRIMARY_FAILED_COMPLETENESS_EXPLORATORY_AVAILABLE_PAIRS_COMPLETED**. Preferred100+100 and minimum30+30 not achieved. New C has {'legitimate': 1, 'phishing': 11}, complete trajectories {'phishing': 0, 'legitimate': 0}, 14 approved rewrite pairs. Prior v3 final_run is untouched.

## 1. Research questions

RQ-C1 asks whether recall changes; C2 which condition moves probabilities most; C3 which causes crossings; C4 how surface distance accompanies movement; C5 whether model decisions differ in stability; C6 whether classes differ; C7 whether false positives are created or recovered. Zero complete cases leave the primary questions unanswered. Available-pair descriptions below are conditional observations.

## 2. Relationship to v1/v2/v3

Historical protocols remain separate. Preserved v3 final_run has195 sources,186 phishing,9 legitimate,39 approved rewrite pairs,7 complete phishing trajectories,0 complete legitimate trajectories and0 observed crossings. Nothing from this new run is merged into those numbers. See RESULTS_CHANGELOG.md.

## 3. Phase architecture

A: historical original-message detection. B: historical source generalization, with a single-class Gateway test. C: this additive rewrite experiment. See PHASE_MAP.md. A/B were not rerun or used to tune the new rewrites.

## 4. Source acquisition

Rescanned67,380 existing raw records across NUS, Mendeley and UCI. Expanded lexical screening found707 new uncertain candidates; these are not707 legitimate controls. No new SMS release with established English institutional-control rights was acquired. Another23 candidates survived a bounded400-candidate phishing-family screen. See SOURCE_EXPANSION_AUDIT.md and its primary-source evidence.

## 5. Rights and provenance

| source_dataset | label | origin_type | N |
| --- | --- | --- | --- |
| gateway | phishing | uncertain_origin | 9 |
| mendeley | phishing | real_source | 2 |
| nus | legitimate | real_source | 1 |

NUS author unlimited-use declaration, Mendeley/UCI CC BY4 and Gateway MIT data release are distinct rights bases. Real-source origin means observed source provenance, not authenticated bank authorship. Synthetic primary controls were not added. Sting9 was not accessed without newly established access and rights.

## 6. Cohort construction

**PRIMARY_FAILED_COMPLETENESS_EXPLORATORY_AVAILABLE_PAIRS_COMPLETED**. Preferred100+100 and minimum30+30 not achieved. New C has {'legitimate': 1, 'phishing': 11}, complete trajectories {'phishing': 0, 'legitimate': 0}, 14 approved rewrite pairs. Prior v3 final_run is untouched.
Every C0 was screened against primary v3 fitting and validation exact/template families. Sampling uses source-only fixed hash order. Models and splits remain unchanged. The finite inspected pool is not proof that no additional valid public source exists.

## 7. Source review

Reviewed1,065 distinct source candidates with separate A/B contexts and adjudication where eligible. Sixteen automatic approvals preceded four documented source-policy exclusions, leaving12 C0 sources. Twelve connection failures received at most one technical recovery with identical payloads; original failures remain preserved. Four exclusions changed eligibility, not class labels. These judgments are automated, not independent human annotation.

## 8. Prompt design

Ten exact external v1 prompts were frozen before scoring: source A/B/J, generation C1/C4/C5/C6 and rewrite A/B/J. Registry SHA-256: 1448f3c41c63a575177c723b3d642fd3b35ea20edd4a8b94bca1187cf4ba8c93. No prompt or model was changed using detector results. See PROMPT_CHANGELOG.md.

## 9. Generation

12 frames yielded 48 initial jobs and 41 permitted quality retries, with 89 actual generated attempts. Retries addressed deterministic quality failures only. Missing technical generation evidence never authorizes a quality retry. Failed outputs and reasons remain in attempts.csv and raw calls.

## 10. Rewrite review

14 condition pairs were approved; 34 initial slots remained rejected/unresolved. Approval counts: {'C1': 2, 'C4': 5, 'C5': 4, 'C6': 3}. Every actual attempt received deterministic and A/B semantic review; J addressed boolean disagreements. Semantic acceptance cannot override literal or condition failures. No further regeneration was used to manufacture completeness.

## 11. Manipulation validation

All approved variants have Jaccard, normalized edit, frozen lexical TF-IDF cosine and prespecified surface-distance measurements. Condition overlap and failures are saved. C6 versus C1 ordering is measured rather than forced. Numerical semantic similarity is unavailable; binary review approval is not embedding similarity. Zero complete cases prevent a primary all-condition manipulation claim.

## 12. Model freeze

| frozen_at | model_name | model_path | sha256 | threshold | training_config_hash | training_dataset_hash |
| --- | --- | --- | --- | --- | --- | --- |
| 2026-11-07T10:21:34.589342+00:00 | LR | models/benchmark_v3/final_run/primary/lexical/LR.joblib | df89f5e2b629b09f3e3f9fe2b6830726bd2d9eb17e5e51f3cdbf8f8a2dedb7bf | 0.5 | 4a32ec0e9674037e9b22bd2801dc003ce9f73e4da48968729ffb34a2a3bdd03b | e5fa9d7277ff19b78c21f8d7e79eb088b5dc5583792f31de186747d5bacdc74f |
| 2026-11-07T10:21:34.589342+00:00 | RF | models/benchmark_v3/final_run/primary/lexical/RF.joblib | 19be45a63832fa8670849a824db84ba37b9fe7b405ae9a7df7776d5aa8147bb7 | 0.5 | 4a32ec0e9674037e9b22bd2801dc003ce9f73e4da48968729ffb34a2a3bdd03b | e5fa9d7277ff19b78c21f8d7e79eb088b5dc5583792f31de186747d5bacdc74f |
| 2026-11-07T10:21:34.589342+00:00 | ModernBERT | models/benchmark_v3/final_run/modernbert/best_checkpoint/model.safetensors | 7ea2311d32ef766a51e3ccc25046f81c8bcdf80d6e3c07b3e42140822af25d43 | 0.5 | c163032a945a89e8221f3cc7aff99a1feed85fb5bb28a6dd7c4f3622d215ff72 | e5fa9d7277ff19b78c21f8d7e79eb088b5dc5583792f31de186747d5bacdc74f |

The unchanged v3 primary models were frozen before new generation. ModernBERT was actually fine-tuned in v3; v3.2 only performs frozen inference. No model retraining or tuning occurred.

## 13. Phase A reference

Historical v3 only: all three models had TP28, FP1, TN0 and FN0 on29 messages. F1=.982456 coexisted with failure on the sole legitimate control. A constant-phishing classifier matches these threshold metrics. This is not a new detection benchmark.

## 14. Phase B reference

Historical v3 only: LR/RF detected167/167 Gateway phishing messages; separately fitted ModernBERT detected147/167. This selected, single-class source test supports no legitimate FPR, temporal robustness or universal ranking.

## 15. Phase C primary results

**NOT RUN: zero complete C0/C1/C4/C5/C6 trajectories.** Primary metrics and24 planned paired p-values are undefined, not zero effects or nonsignificance.

| analysis_id | hypothesis | N_frames | N_rows | model | condition | effect_size | CI | raw_p | adjusted_p | confirmatory_or_exploratory | notes | N_phishing | N_legitimate | LR_mean_absolute_delta | RF_mean_absolute_delta | ModernBERT_mean_absolute_delta | LR_recall | LR_false_positive_rate | LR_specificity | LR_false_negative_rate | LR_accuracy | LR_N_positive | LR_N_negative | RF_recall | RF_false_positive_rate | RF_specificity | RF_false_negative_rate | RF_accuracy | RF_N_positive | RF_N_negative | ModernBERT_recall | ModernBERT_false_positive_rate | ModernBERT_specificity | ModernBERT_false_negative_rate | ModernBERT_accuracy | ModernBERT_N_positive | ModernBERT_N_negative |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| primary_condition_performance | primary_condition_performance | 0 | 0 | LR/RF/ModernBERT | C0 | nan | nan | nan | nan | exploratory | Primary complete cohort. Recall/FNR and FPR/specificity are class-specific. Accuracy and mean absolute delta combine classes; probability effects by class are reported separately. | 0 | 0 | nan | nan | nan | nan | nan | nan | nan | nan | 0 | 0 | nan | nan | nan | nan | nan | 0 | 0 | nan | nan | nan | nan | nan | 0 | 0 |
| primary_condition_performance | primary_condition_performance | 0 | 0 | LR/RF/ModernBERT | C1 | nan | nan | nan | nan | exploratory | Primary complete cohort. Recall/FNR and FPR/specificity are class-specific. Accuracy and mean absolute delta combine classes; probability effects by class are reported separately. | 0 | 0 | nan | nan | nan | nan | nan | nan | nan | nan | 0 | 0 | nan | nan | nan | nan | nan | 0 | 0 | nan | nan | nan | nan | nan | 0 | 0 |
| primary_condition_performance | primary_condition_performance | 0 | 0 | LR/RF/ModernBERT | C4 | nan | nan | nan | nan | exploratory | Primary complete cohort. Recall/FNR and FPR/specificity are class-specific. Accuracy and mean absolute delta combine classes; probability effects by class are reported separately. | 0 | 0 | nan | nan | nan | nan | nan | nan | nan | nan | 0 | 0 | nan | nan | nan | nan | nan | 0 | 0 | nan | nan | nan | nan | nan | 0 | 0 |
| primary_condition_performance | primary_condition_performance | 0 | 0 | LR/RF/ModernBERT | C5 | nan | nan | nan | nan | exploratory | Primary complete cohort. Recall/FNR and FPR/specificity are class-specific. Accuracy and mean absolute delta combine classes; probability effects by class are reported separately. | 0 | 0 | nan | nan | nan | nan | nan | nan | nan | nan | 0 | 0 | nan | nan | nan | nan | nan | 0 | 0 | nan | nan | nan | nan | nan | 0 | 0 |
| primary_condition_performance | primary_condition_performance | 0 | 0 | LR/RF/ModernBERT | C6 | nan | nan | nan | nan | exploratory | Primary complete cohort. Recall/FNR and FPR/specificity are class-specific. Accuracy and mean absolute delta combine classes; probability effects by class are reported separately. | 0 | 0 | nan | nan | nan | nan | nan | nan | nan | nan | 0 | 0 | nan | nan | nan | nan | nan | 0 | 0 | nan | nan | nan | nan | nan | 0 | 0 |


Available-pair metrics are separately saved in available_pair_metrics.csv. Their condition cohorts differ.

## 16. Legitimate controls

Only 1 legitimate C0 and 0 complete legitimate trajectories survive. The named card-registration fraud alert has intelligible financial function, but sender authenticity is unverified. Its rewrites cannot create independent control messages or support population FPR.

## 17. Threshold transitions

| analysis_id | hypothesis | N_frames | N_rows | model | condition | effect_size | CI | raw_p | adjusted_p | confirmatory_or_exploratory | notes | cohort | existing_false_positives | persistent_false_positives | new_false_positives | recoveries |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| available_pair_negative_threshold_transitions | available_pair_negative_threshold_transitions | 1 | 1 | LR | C1 |  |  |  |  | exploratory | Secondary available-pair counts conditional on approved rewrites; separate from complete-case primary cohort. | available_pair | 1 | 1 | 0 | 0 |
| available_pair_negative_threshold_transitions | available_pair_negative_threshold_transitions | 1 | 1 | LR | C4 |  |  |  |  | exploratory | Secondary available-pair counts conditional on approved rewrites; separate from complete-case primary cohort. | available_pair | 1 | 1 | 0 | 0 |
| available_pair_negative_threshold_transitions | available_pair_negative_threshold_transitions | 1 | 1 | LR | C5 |  |  |  |  | exploratory | Secondary available-pair counts conditional on approved rewrites; separate from complete-case primary cohort. | available_pair | 1 | 1 | 0 | 0 |
| available_pair_negative_threshold_transitions | available_pair_negative_threshold_transitions | 0 | 0 | LR | C6 |  |  |  |  | exploratory | Secondary available-pair counts conditional on approved rewrites; separate from complete-case primary cohort. | available_pair | 0 | 0 | 0 | 0 |
| available_pair_negative_threshold_transitions | available_pair_negative_threshold_transitions | 1 | 1 | RF | C1 |  |  |  |  | exploratory | Secondary available-pair counts conditional on approved rewrites; separate from complete-case primary cohort. | available_pair | 1 | 1 | 0 | 0 |
| available_pair_negative_threshold_transitions | available_pair_negative_threshold_transitions | 1 | 1 | RF | C4 |  |  |  |  | exploratory | Secondary available-pair counts conditional on approved rewrites; separate from complete-case primary cohort. | available_pair | 1 | 1 | 0 | 0 |
| available_pair_negative_threshold_transitions | available_pair_negative_threshold_transitions | 1 | 1 | RF | C5 |  |  |  |  | exploratory | Secondary available-pair counts conditional on approved rewrites; separate from complete-case primary cohort. | available_pair | 1 | 1 | 0 | 0 |
| available_pair_negative_threshold_transitions | available_pair_negative_threshold_transitions | 0 | 0 | RF | C6 |  |  |  |  | exploratory | Secondary available-pair counts conditional on approved rewrites; separate from complete-case primary cohort. | available_pair | 0 | 0 | 0 | 0 |
| available_pair_negative_threshold_transitions | available_pair_negative_threshold_transitions | 1 | 1 | ModernBERT | C1 |  |  |  |  | exploratory | Secondary available-pair counts conditional on approved rewrites; separate from complete-case primary cohort. | available_pair | 1 | 1 | 0 | 0 |
| available_pair_negative_threshold_transitions | available_pair_negative_threshold_transitions | 1 | 1 | ModernBERT | C4 |  |  |  |  | exploratory | Secondary available-pair counts conditional on approved rewrites; separate from complete-case primary cohort. | available_pair | 1 | 1 | 0 | 0 |
| available_pair_negative_threshold_transitions | available_pair_negative_threshold_transitions | 1 | 1 | ModernBERT | C5 |  |  |  |  | exploratory | Secondary available-pair counts conditional on approved rewrites; separate from complete-case primary cohort. | available_pair | 1 | 1 | 0 | 0 |
| available_pair_negative_threshold_transitions | available_pair_negative_threshold_transitions | 0 | 0 | ModernBERT | C6 |  |  |  |  | exploratory | Secondary available-pair counts conditional on approved rewrites; separate from complete-case primary cohort. | available_pair | 0 | 0 | 0 | 0 |

Available-pair crossing counts per model: {'LR': 0, 'RF': 0, 'ModernBERT': 0}. Existing C0 false positives, newly created false positives and recoveries are separate quantities. Primary transition tables have no supporting complete frames; their zero counts are not observed primary stability.

## 18. Distance analysis

Primary distance association is unavailable. Separately labelled available-pair frame slopes follow; frames need at least two varying approved rewrites.

| analysis_id | hypothesis | N_frames | N_rows | model | condition | effect_size | CI | raw_p | adjusted_p | confirmatory_or_exploratory | notes | true_label | cohort | ci_lower | ci_upper | bootstrap_replicates | bootstrap_unit | seed |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| available_pair_mean_frame_distance_absolute_movement_slope | available_pair_mean_frame_distance_absolute_movement_slope | 1 | 3 | LR | C1/C4/C5/C6 | 0.026830837998721692 |  |  |  | exploratory | Secondary conditional available-pair summary, separate from primary. Each frame needs at least two approved rewrites with distance variation. Mean within-frame slope, bootstrap whole frames. Selected missingness prevents causal interpretation; unsupported quantities blank. | 0 | available_pair |  |  | 2000 | frame | 42 |
| available_pair_mean_frame_distance_absolute_movement_slope | available_pair_mean_frame_distance_absolute_movement_slope | 1 | 3 | LR | C1/C4/C5/C6 | 0.02330172065303442 |  |  |  | exploratory | Secondary conditional available-pair summary, separate from primary. Each frame needs at least two approved rewrites with distance variation. Mean within-frame slope, bootstrap whole frames. Selected missingness prevents causal interpretation; unsupported quantities blank. | 1 | available_pair |  |  | 2000 | frame | 42 |
| available_pair_mean_frame_distance_absolute_movement_slope | available_pair_mean_frame_distance_absolute_movement_slope | 1 | 3 | RF | C1/C4/C5/C6 | 0.03423604744044896 |  |  |  | exploratory | Secondary conditional available-pair summary, separate from primary. Each frame needs at least two approved rewrites with distance variation. Mean within-frame slope, bootstrap whole frames. Selected missingness prevents causal interpretation; unsupported quantities blank. | 0 | available_pair |  |  | 2000 | frame | 42 |
| available_pair_mean_frame_distance_absolute_movement_slope | available_pair_mean_frame_distance_absolute_movement_slope | 1 | 3 | RF | C1/C4/C5/C6 | 0.0477769031823912 |  |  |  | exploratory | Secondary conditional available-pair summary, separate from primary. Each frame needs at least two approved rewrites with distance variation. Mean within-frame slope, bootstrap whole frames. Selected missingness prevents causal interpretation; unsupported quantities blank. | 1 | available_pair |  |  | 2000 | frame | 42 |
| available_pair_mean_frame_distance_absolute_movement_slope | available_pair_mean_frame_distance_absolute_movement_slope | 1 | 3 | ModernBERT | C1/C4/C5/C6 | 0.40376709807493383 |  |  |  | exploratory | Secondary conditional available-pair summary, separate from primary. Each frame needs at least two approved rewrites with distance variation. Mean within-frame slope, bootstrap whole frames. Selected missingness prevents causal interpretation; unsupported quantities blank. | 0 | available_pair |  |  | 2000 | frame | 42 |
| available_pair_mean_frame_distance_absolute_movement_slope | available_pair_mean_frame_distance_absolute_movement_slope | 1 | 3 | ModernBERT | C1/C4/C5/C6 | 0.0010097035896673972 |  |  |  | exploratory | Secondary conditional available-pair summary, separate from primary. Each frame needs at least two approved rewrites with distance variation. Mean within-frame slope, bootstrap whole frames. Selected missingness prevents causal interpretation; unsupported quantities blank. | 1 | available_pair |  |  | 2000 | frame | 42 |

No association establishes linguistic causality. Missing conditions and selected approvals constrain interpretation.

## 19. Model comparison

No primary model-by-condition comparison is estimable. Available-pair score effects are descriptive and class-specific:

| analysis_id | hypothesis | N_frames | N_rows | model | condition | effect_size | CI | raw_p | adjusted_p | confirmatory_or_exploratory | notes | true_label | cohort | mean_signed_delta | mean_absolute_delta | signed_ci_lower | signed_ci_upper | absolute_delta_CI | absolute_ci_lower | absolute_ci_upper | bootstrap_unit | bootstrap_replicates | seed |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| available_pair_probability_effects | available_pair_probability_effects | 1 | 1 | LR | C1 | 0.0 |  |  |  | exploratory | Secondary class-separated available-pair effects conditional on approved rewrites, not primary inference. Signed P0-Pi. Bootstrap whole frames; fewer than two frames gives no CI; no causal interpretation. | 0 | available_pair | 0.0 | 0.0 |  |  |  |  |  | frame | 2000 | 42 |
| available_pair_probability_effects | available_pair_probability_effects | 1 | 1 | LR | C1 | 0.0006548239081034524 |  |  |  | exploratory | Secondary class-separated available-pair effects conditional on approved rewrites, not primary inference. Signed P0-Pi. Bootstrap whole frames; fewer than two frames gives no CI; no causal interpretation. | 1 | available_pair | 0.0006548239081034524 | 0.0006548239081034524 |  |  |  |  |  | frame | 2000 | 42 |
| available_pair_probability_effects | available_pair_probability_effects | 1 | 1 | LR | C4 | -0.0011324396297341943 |  |  |  | exploratory | Secondary class-separated available-pair effects conditional on approved rewrites, not primary inference. Signed P0-Pi. Bootstrap whole frames; fewer than two frames gives no CI; no causal interpretation. | 0 | available_pair | -0.0011324396297341943 | 0.0011324396297341943 |  |  |  |  |  | frame | 2000 | 42 |
| available_pair_probability_effects | available_pair_probability_effects | 4 | 4 | LR | C4 | -0.0002484497205612335 | [-0.001058897792, 0.0003044807021] |  |  | exploratory | Secondary class-separated available-pair effects conditional on approved rewrites, not primary inference. Signed P0-Pi. Bootstrap whole frames; fewer than two frames gives no CI; no causal interpretation. | 1 | available_pair | -0.0002484497205612335 | 0.000552930422707848 | -0.0010588977918015996 | 0.0003044807021466145 | [0.000167864861, 0.00116752266] | 0.0001678648610354827 | 0.001167522660252801 | frame | 2000 | 42 |
| available_pair_probability_effects | available_pair_probability_effects | 1 | 1 | LR | C5 | -0.0037547890079613344 |  |  |  | exploratory | Secondary class-separated available-pair effects conditional on approved rewrites, not primary inference. Signed P0-Pi. Bootstrap whole frames; fewer than two frames gives no CI; no causal interpretation. | 0 | available_pair | -0.0037547890079613344 | 0.0037547890079613344 |  |  |  |  |  | frame | 2000 | 42 |
| available_pair_probability_effects | available_pair_probability_effects | 3 | 3 | LR | C5 | 0.0 | [0, 0] |  |  | exploratory | Secondary class-separated available-pair effects conditional on approved rewrites, not primary inference. Signed P0-Pi. Bootstrap whole frames; fewer than two frames gives no CI; no causal interpretation. | 1 | available_pair | 0.0 | 0.0 | 0.0 | 0.0 | [0, 0] | 0.0 | 0.0 | frame | 2000 | 42 |
| available_pair_probability_effects | available_pair_probability_effects | 0 | 0 | LR | C6 |  |  |  |  | exploratory | Secondary class-separated available-pair effects conditional on approved rewrites, not primary inference. Signed P0-Pi. Bootstrap whole frames; fewer than two frames gives no CI; no causal interpretation. | 0 | available_pair |  |  |  |  |  |  |  | frame | 2000 | 42 |
| available_pair_probability_effects | available_pair_probability_effects | 3 | 3 | LR | C6 | 0.0038136815466380445 | [0.0015484799, 0.007726000865] |  |  | exploratory | Secondary class-separated available-pair effects conditional on approved rewrites, not primary inference. Signed P0-Pi. Bootstrap whole frames; fewer than two frames gives no CI; no causal interpretation. | 1 | available_pair | 0.0038136815466380445 | 0.0038136815466380445 | 0.0015484798995697435 | 0.0077260008645736455 | [0.0015484799, 0.007726000865] | 0.0015484798995697435 | 0.0077260008645736455 | frame | 2000 | 42 |
| available_pair_probability_effects | available_pair_probability_effects | 1 | 1 | RF | C1 | 0.0 |  |  |  | exploratory | Secondary class-separated available-pair effects conditional on approved rewrites, not primary inference. Signed P0-Pi. Bootstrap whole frames; fewer than two frames gives no CI; no causal interpretation. | 0 | available_pair | 0.0 | 0.0 |  |  |  |  |  | frame | 2000 | 42 |
| available_pair_probability_effects | available_pair_probability_effects | 1 | 1 | RF | C1 | 0.0 |  |  |  | exploratory | Secondary class-separated available-pair effects conditional on approved rewrites, not primary inference. Signed P0-Pi. Bootstrap whole frames; fewer than two frames gives no CI; no causal interpretation. | 1 | available_pair | 0.0 | 0.0 |  |  |  |  |  | frame | 2000 | 42 |
| available_pair_probability_effects | available_pair_probability_effects | 1 | 1 | RF | C4 | 0.0 |  |  |  | exploratory | Secondary class-separated available-pair effects conditional on approved rewrites, not primary inference. Signed P0-Pi. Bootstrap whole frames; fewer than two frames gives no CI; no causal interpretation. | 0 | available_pair | 0.0 | 0.0 |  |  |  |  |  | frame | 2000 | 42 |
| available_pair_probability_effects | available_pair_probability_effects | 4 | 4 | RF | C4 | -0.0012500000000000011 | [-0.00375, 0] |  |  | exploratory | Secondary class-separated available-pair effects conditional on approved rewrites, not primary inference. Signed P0-Pi. Bootstrap whole frames; fewer than two frames gives no CI; no causal interpretation. | 1 | available_pair | -0.0012500000000000011 | 0.0012500000000000011 | -0.0037500000000000033 | 0.0 | [0, 0.00375] | 0.0 | 0.0037500000000000033 | frame | 2000 | 42 |
| available_pair_probability_effects | available_pair_probability_effects | 1 | 1 | RF | C5 | -0.0050000000000000044 |  |  |  | exploratory | Secondary class-separated available-pair effects conditional on approved rewrites, not primary inference. Signed P0-Pi. Bootstrap whole frames; fewer than two frames gives no CI; no causal interpretation. | 0 | available_pair | -0.0050000000000000044 | 0.0050000000000000044 |  |  |  |  |  | frame | 2000 | 42 |
| available_pair_probability_effects | available_pair_probability_effects | 3 | 3 | RF | C5 | 0.0 | [0, 0] |  |  | exploratory | Secondary class-separated available-pair effects conditional on approved rewrites, not primary inference. Signed P0-Pi. Bootstrap whole frames; fewer than two frames gives no CI; no causal interpretation. | 1 | available_pair | 0.0 | 0.0 | 0.0 | 0.0 | [0, 0] | 0.0 | 0.0 | frame | 2000 | 42 |
| available_pair_probability_effects | available_pair_probability_effects | 0 | 0 | RF | C6 |  |  |  |  | exploratory | Secondary class-separated available-pair effects conditional on approved rewrites, not primary inference. Signed P0-Pi. Bootstrap whole frames; fewer than two frames gives no CI; no causal interpretation. | 0 | available_pair |  |  |  |  |  |  |  | frame | 2000 | 42 |
| available_pair_probability_effects | available_pair_probability_effects | 3 | 3 | RF | C6 | -0.00833333333333334 | [-0.04, 0.015] |  |  | exploratory | Secondary class-separated available-pair effects conditional on approved rewrites, not primary inference. Signed P0-Pi. Bootstrap whole frames; fewer than two frames gives no CI; no causal interpretation. | 1 | available_pair | -0.00833333333333334 | 0.01833333333333335 | -0.040000000000000036 | 0.015000000000000013 | [0, 0.04] | 0.0 | 0.040000000000000036 | frame | 2000 | 42 |
| available_pair_probability_effects | available_pair_probability_effects | 1 | 1 | ModernBERT | C1 | -0.004338085651397705 |  |  |  | exploratory | Secondary class-separated available-pair effects conditional on approved rewrites, not primary inference. Signed P0-Pi. Bootstrap whole frames; fewer than two frames gives no CI; no causal interpretation. | 0 | available_pair | -0.004338085651397705 | 0.004338085651397705 |  |  |  |  |  | frame | 2000 | 42 |
| available_pair_probability_effects | available_pair_probability_effects | 1 | 1 | ModernBERT | C1 | 0.0006172060966490589 |  |  |  | exploratory | Secondary class-separated available-pair effects conditional on approved rewrites, not primary inference. Signed P0-Pi. Bootstrap whole frames; fewer than two frames gives no CI; no causal interpretation. | 1 | available_pair | 0.0006172060966490589 | 0.0006172060966490589 |  |  |  |  |  | frame | 2000 | 42 |
| available_pair_probability_effects | available_pair_probability_effects | 1 | 1 | ModernBERT | C4 | -0.01790475845336914 |  |  |  | exploratory | Secondary class-separated available-pair effects conditional on approved rewrites, not primary inference. Signed P0-Pi. Bootstrap whole frames; fewer than two frames gives no CI; no causal interpretation. | 0 | available_pair | -0.01790475845336914 | 0.01790475845336914 |  |  |  |  |  | frame | 2000 | 42 |
| available_pair_probability_effects | available_pair_probability_effects | 4 | 4 | ModernBERT | C4 | -0.00044821202754974365 | [-0.000936627388, 1.488626003e-05] |  |  | exploratory | Secondary class-separated available-pair effects conditional on approved rewrites, not primary inference. Signed P0-Pi. Bootstrap whole frames; fewer than two frames gives no CI; no causal interpretation. | 1 | available_pair | -0.00044821202754974365 | 0.0005912631750107367 | -0.0009366273880005715 | 1.4886260032737075e-05 | [0.0002918541431, 0.0008906722069] | 0.0002918541431427557 | 0.0008906722068787176 | frame | 2000 | 42 |
| available_pair_probability_effects | available_pair_probability_effects | 1 | 1 | ModernBERT | C5 | -0.06134486198425304 |  |  |  | exploratory | Secondary class-separated available-pair effects conditional on approved rewrites, not primary inference. Signed P0-Pi. Bootstrap whole frames; fewer than two frames gives no CI; no causal interpretation. | 0 | available_pair | -0.06134486198425304 | 0.06134486198425304 |  |  |  |  |  | frame | 2000 | 42 |
| available_pair_probability_effects | available_pair_probability_effects | 3 | 3 | ModernBERT | C5 | 0.0011829535166423637 | [-0.0004907250404, 0.00318801403] |  |  | exploratory | Secondary class-separated available-pair effects conditional on approved rewrites, not primary inference. Signed P0-Pi. Bootstrap whole frames; fewer than two frames gives no CI; no causal interpretation. | 1 | available_pair | 0.0011829535166423637 | 0.0015101035435994097 | -0.000490725040435569 | 0.003188014030456654 | [0.0004907250404, 0.00318801403] | 0.000490725040435569 | 0.003188014030456654 | frame | 2000 | 42 |
| available_pair_probability_effects | available_pair_probability_effects | 0 | 0 | ModernBERT | C6 |  |  |  |  | exploratory | Secondary class-separated available-pair effects conditional on approved rewrites, not primary inference. Signed P0-Pi. Bootstrap whole frames; fewer than two frames gives no CI; no causal interpretation. | 0 | available_pair |  |  |  |  |  |  |  | frame | 2000 | 42 |
| available_pair_probability_effects | available_pair_probability_effects | 3 | 3 | ModernBERT | C6 | 0.00033917029698682377 | [7.390975952e-05, 0.0007555484772] |  |  | exploratory | Secondary class-separated available-pair effects conditional on approved rewrites, not primary inference. Signed P0-Pi. Bootstrap whole frames; fewer than two frames gives no CI; no causal interpretation. | 1 | available_pair | 0.00033917029698682377 | 0.00033917029698682377 | 7.390975952137335e-05 | 0.0007555484771728516 | [7.390975952e-05, 0.0007555484772] | 7.390975952137335e-05 | 0.0007555484771728516 | frame | 2000 | 42 |

Probability movement and threshold stability answer different questions. No universal best model follows.

## 20. Statistical inference

The SAP froze before scoring:24 primary McNemar/Holm hypotheses and24 secondary paired-model contrasts, with frame bootstrap2,000 draws and seed42. With no complete cases, primary tests and model interactions are NOT RUN. Available-pair intervals remain exploratory; one-frame support is not converted into a population confidence claim.

## 21. Extreme cases

The strongest individual available-pair movement is explicitly an extreme, not representative:

{"C0_probability": 0.8684853315353394, "absolute_delta": 0.0613448619842529, "condition": "C5", "frame_id": "nus-5294", "model": "ModernBERT", "model_sha256": "7ea2311d32ef766a51e3ccc25046f81c8bcdf80d6e3c07b3e42140822af25d43", "prediction": 1, "primary_complete_case": false, "probability": 0.9298301935195924, "signed_delta": -0.0613448619842529, "surface_distance": 0.235263432446531, "text_sha256": "a92401c3308234c5a6b108e8f30d03da4015588671e5257b5850531cbbec4158", "threshold_transition": "1->1", "true_label": 0}

## 22. Representative case

**Unavailable:** no complete frame exists for the prespecified nearest-median complete-trajectory selection rule. Figure9 is an annotated unavailable result, not an invented or incomplete primary trajectory.

## 23. Limitations

## Dataset limitations
Only one eligible legitimate source remains; its sender authenticity/origin is unresolved. Known real-source provenance is not proof of bank authorship. Rights-cleared does not establish label truth. Source imbalance, conservative family exclusions and finite candidate search limit population coverage.
## Model limitations
Reuse of small, imbalanced v3-trained models; probability outputs are uncalibrated. This experiment does not retrain or improve detectors. Frozen-artifact identity does not imply deployment quality.
## Generation limitations
Four conditions can overlap in actual surface changes; exact institution/numeric/placeholders constrain transformations. Rejected attempts and selective completeness produce survivorship effects. No outcome-driven rewrite optimization.
## Automated review limitations
Separate contexts are not statistically independent human annotation. Shared provider/model biases remain; generator and A share a snapshot. Confidence is subjective. Four initial source approvals required source-only policy exclusion, demonstrating fallibility.
## Statistical limitations
Below30legitimateframes, no adequately supported between-class or model-by-condition population comparison. Frame bootstrap cannot create support, and a degenerate interval on one control is not certainty. Conditions are repeated within frames; primary and available-pair cohorts differ.
## External validity limitations
Defanged public historical SMS are not representative current bank traffic. Prior pool inspection and review failures affect selection. No deployment FPR, temporal drift or universal model ranking.
## Causal inference limitations
Descriptive associations between surface distance and score movement do not establish linguistic causality. Semantic preservation is model-judged, not independently verified ground truth; no numeric semantic embedding similarity was measured.


## 24. Safe claims

A separate detector-blind protocol was executed with exact source, prompt, request, review, model and prediction evidence. Its cohort and completeness targets failed. Selected available-pair changes can be described with actual N, without calling the primary experiment successful.

## 25. Unsafe claims

Do not claim30+30 or100+100 completion, independent human truth, primary significance, general robustness, current banking FPR, causal linguistic effects or contextual-model superiority. Missing conditions are not zero effects.

## 26. What changed from previous run

New source screening, prospective external prompts and SAP, fresh generation/review calls and separately versioned results were added. Existing v3 data, models, outputs and FINAL_REPORT.md are unchanged. The ambiguous native ID and four source-policy exclusions were documented before generation. No old39-pair result was reinterpreted.

## 27. Recommended next work

Acquire rights-cleared real institutional controls with independent human adjudication and new family diversity. Prospectively redesign the generation instrument after examining preserved condition failures, then start a new frozen run. Do not relax this run’s acceptance rules or repeat it until desired completeness or scores appear.
