# Benchmark v3 final research report

**Status: corrected exploratory benchmark completed; intended balanced benchmark and primary robustness experiment remain unmet.** Only `data/benchmark_v3/corrected_run`, `models/benchmark_v3/corrected_run` and `results/benchmark_v3/corrected_run` supply current scientific results. The preserved original 231-family run is INVALIDATED by confirmed cross-split template leakage. Its figures and scores must not be presented as current evidence.

The strongest finding is a measurement limitation: all three models achieved F1 0.9851 while misclassifying the sole legitimate held-out control. These results do not establish useful financial-SMS discrimination. Machine review, scarce controls and retrospective correction make every comparison exploratory.

## 1. Data acquisition

The acquisition contains 234,547 raw records across eight dataset groups. SMISH_DT was used as a source locator and immutable acquisition container, never as a single ground-truth source. The acquisition manifest records revision, retrieval and file hashes. English screening retained 209,827 candidates; financial screening retained 37,063; exact duplicate excess was 13,625, leaving 23,438 unique financial candidates. Rights eligibility left 12,247 candidates. Screening counts are not validated labels or independent observations. The provider-call ledger records 189 source-review requests (85 invalidated v3.0 instrument calls and 104 v3.1 calls including two policy rechecks), plus 31 supplement requests: 220 total. Recorded actual usage is 470,337 input and 197,502 output tokens. Instrument-invalidated calls are not silently counted as valid labels.

Sting9 contributed zero rows: export access returned HTTP 401 without configured credentials, and the documented dump attempt returned 404. Retrieved pages had conflicting license statements. See [Sting9 audit](STING9_ACCESS_AND_LICENSE_AUDIT.md). No credentials were invented, submissions created, or raw Sting9 data redistributed.

## 2. Source provenance

The corrected final cohort contains 228 template families/messages: Gateway 194, Mendeley 27, NUS 6 and UCI 1. These are four nominal dataset groups, not four independent populations: UCI includes NUS material, and Mendeley acknowledges previous corpora. Cross-source provenance is retained through deduplication. Original row identifiers and original labels remain separate from reviewed canonical labels.

Origin accounting is 34 real-source observations, 194 uncertain-origin observations and zero synthetic observations. Here real means observed non-synthetic source provenance; it does not establish authenticated human origin or verified bank authorship. Gateway provenance does not establish individual-message origin and is reported uncertain. Engineering feasibility fixtures are separate and never enter this cohort.

## 3. License findings

[Source rights audit](SOURCE_LICENSE_AUDIT.md) and `data/benchmark_v3/provenance/upstream_rights_evidence.json` hold the evidence. [Mendeley v1](https://data.mendeley.com/datasets/f45bkkt8pr/1) and [UCI #228](https://archive.ics.uci.edu/dataset/228/sms+spam+collection) explicitly state CC BY 4.0; attribution, license links and modification notices apply. The [NUS authors' paper](https://arxiv.org/html/1112.2468), sections 4.4 and 6, describes a public-domain release and copyright-free unlimited use; this is an author declaration, not an invented CC0 license. The [Gateway repository](https://github.com/wspr-ncsu/sms-phishing) explicitly releases data under its repository MIT notice; retain that notice. ExAIS, Super SMS, SpamHunter and SmishTank were investigated but remain excluded from modeling because an adequate original reuse grant was not retrieved. Aggregator access does not override those rights.

## 4. Label harmonization

Canonical labels are phishing, legitimate, uncertain and exclude. Generic spam was never universally equated with phishing, nor ham with banking legitimacy. Explicit smishing labels are candidates; financial intent, channel and function still require review. The final reviewed cohort contains 219 phishing and nine legitimate messages. These are machine-reviewed research labels, not independent human ground truth. See [label policy](LABEL_POLICY.md).

## 5. Banking filter

Keyword/entity screening was followed by source-blind semantic policy review and provenance checks. Functions include security/restriction, transactions, payments/transfers, cards, fraud, verification/refunds and financial services. Mere money vocabulary, generic OTP or personal coordination does not establish a legitimate financial-service notification. There were 707 fresh v3.1 source reviews; 314 were initially approved, and two further policy exclusions left 312. During correction, Mendeley row 4 and NUS row 5489 were excluded after fresh source-only policy reassessment. These decisions preceded corrected fitting and did not change model hyperparameters.

## 6. Defanging

Training/evaluation exports use typed URL, phone, email, account and transaction placeholders. Dates/times are handled separately to avoid misclassifying ordinary dates as phones. Financial amounts and ordinary banking language are retained where appropriate. Seven upstream encoding flags remain disclosed; no post-score text repair was performed. This avoids silently changing evaluated inputs but leaves a source-quality limitation.

## 7. Duplicate removal

Exact normalization produced 13,625 duplicate excess records among financial candidates. Duplicate origins are retained for provenance rather than counted as independent examples. Exact hashes and safe normalized text support audit; exact uniqueness alone does not imply template independence.

## 8. Template-family construction

Placeholder-normalized structure and lexical similarity support family grouping. The approved 312 rows lost 84 additional template observations, leaving 228 families. Independent audit identified the Shijo/Sinco payee-registration template spanning train and test in the original run. That run is preserved and invalidated. Correction broadened template grouping and rebuilt cohorts before fresh fits. The corrected run's family integrity is the relevant leakage result; residual undetected semantic templates remain possible.

## 9. Final sample

| Quantity | Corrected count |
|---|---:|
| Final independent family representatives | 228 |
| Phishing | 219 |
| Legitimate | 9 |
| Real-source observations | 34 |
| Uncertain origin | 194 |
| Synthetic | 0 |
| Nominal dataset groups | 4 |

The desired minimum of 300 phishing and 300 legitimate controls was not reached. Raw collection scale cannot substitute for rights-cleared, policy-valid and independently templated controls. This cohort is unsuitable for deployment or a confirmatory claim of contextual superiority.

## 10. Split methodology

Primary family-grouped split: train 160 (153 phishing/7 legitimate), validation 34 (33/1), held-out test 34 (33/1). Fixed protocol and validation-only selection were used for all three models on the same cohort. A separate source experiment trains on 29 (21/8), validates on five (4/1), and tests on 194 Gateway phishing messages. Those are separately fitted models, not primary models scored on an additional test set. No legitimate Gateway test controls exist.

The test pool had already been inspected in the original run before the correction. Even with unchanged hyperparameters, the corrected comparison is exploratory rather than a fresh confirmatory holdout.

## 11. Leakage audit

The original run failed template isolation and is not rescued by its earlier checks. Corrected cohort and model manifests record frozen input/protocol hashes, broader family boundaries and artifact integrity. Exact/template overlap, source isolation, training partition access and rewrite separation are checked by implementation guards and tests. No rewrite enters fitting; threshold remains 0.5. The corrected `results/benchmark_v3/corrected_run/verification.json` passed: 1,044 historical files were checked with zero changes; direct source-approval/rewrite/raw-provider hash bindings, source isolation, train-only TF-IDF reconstruction and frozen model hashes were verified. Ten figures and 16 tables were verified. Consult the final verification receipt and `TEST_RESULTS.md` for the final suite totals.

## 12. Logistic Regression training

LR uses TF-IDF word-pattern features and a linear logistic decision rule. It was refitted on the corrected training cohort using the fixed configuration; validation/test rows were excluded from feature fitting. Its primary artifact hash is `2bf761f765c22ab418d15c596e7a454b7db8d70f39ec346eec9b0058fdd01e4f`. The source-holdout experiment has a separate fit and manifest.

## 13. Random Forest training

RF uses the same TF-IDF representation with nonlinear tree decisions. It was refitted on the same corrected fitting partitions under its unchanged configuration. Its primary artifact hash is `774565ec21111867d26dc8c0874fcab2da363e89d3da110c9cf864ae821ec104`. Neither lexical model was tuned against corrected test performance.

## 14. ModernBERT training

`answerdotai/ModernBERT-base` revision `8949b909ec900327062f0ebf497f51aef5e6f0c8` was loaded with an explicit binary sequence-classification head (0 legitimate, 1 phishing). All 149,606,402 parameters underwent actual CPU fine-tuning for two epochs; this was not fill-mask inference, an alternate checkpoint, or a frozen-encoder substitute. CUDA/MPS were unavailable. A dedicated environment and reproducible full-parameter feasibility test established execution feasibility; [training/feasibility evidence](MODERNBERT_FEASIBILITY.md) records versions, hardware, configuration and source SHA-256.

Both corrected fits reused the same seed 42, AdamW configuration, learning rate, batch size, two-epoch schedule, validation-loss selection rule and maximum length 128. Primary validation selected epoch 1 (cross entropy 0.0839967); source-holdout selected epoch 2 (0.3920023). These losses are checkpoint-selection evidence, not held-out detection performance. Primary model weights SHA-256: `2f22676530245bcbd2492e0ef406e1b2abad8712a4be96b90897fc31bba5e7b4`. Source-holdout weights: `829fdb7b674765099413ada0473454a888169531289fa2f501bd8f8880b2389c`. Manifests and artifact integrity were checked after fitting. Twenty dedicated ModernBERT tests passed, including real tokenizer/model checks and added protocol guards.

## 15. Experiment A: original detection

All three models predicted phishing for every one of the same 34 test messages. Each has TP=33, FP=1, TN=0, FN=0; accuracy and precision 0.970588, recall 1, F1 0.985075, specificity 0, FNR 0 and FPR 1. A constant-phishing classifier yields the same threshold metrics. ROC-AUC and PR-AUC are numerically 1 because the single negative ranks below positives, but this one-negative ranking does not establish reliable discrimination or calibration. Scores were not independently calibrated.

Exact 95% intervals are accuracy [0.8467, 0.9993], recall [0.8942, 1], and FPR [0.025, 1]. The single control makes FPR highly uncertain. See corrected tables 04 and 08. RQ1 cannot be answered as a general accuracy claim for legitimate financial SMS.

## 16. Experiment B: source/temporal generalization

On 194 held-out Gateway phishing messages, separately trained LR and RF detect 194/194; ModernBERT detects 169/194 (recall 0.871134; 25 false negatives). No specificity, FPR or ROC/PR discrimination estimate is available from a single-class test. These results describe selected machine-reviewed Gateway phishing, not a causal effect of representation or reliable generalization to all sources. Source composition and source-specific labeling can confound the difference.

Temporal evaluation was NOT RUN: usable message timestamps were inadequate. Collection dates and repository timestamps are not message dates. RQ2 has limited source-specific recall evidence and no prospective newer-message evidence.

## 17. Experiment C: linguistic robustness

The primary experiment was NOT RUN because the minimum gate of ten legitimate controls was unmet. A separate exploratory supplement reused blind stimuli: 35 original frames, 140 initial variants and 30 quality retries; 51 approved variants and 89 rejected/unresolved initial slots. All 51 required adjudication. One adjudication batch used incorrect IDs and its 20 decisions were excluded rather than silently accepted.

After correction, only still-held-out sources were scored: 34 originals (33 phishing, one legitimate) and 48 approved phishing variants, totaling 82 unique scored rows per frozen model. There are no legitimate rewrites. Available pairs by condition are C1=10, C4=13, C5=12, C6=13; selective quality attrition prevents treating these as a balanced condition experiment. Nine phishing frames have all four conditions and form the complete-frame descriptive core.

Chronology is material: stimuli were generated without detector feedback after the ORIGINAL models were frozen, but before the corrected models were refitted. Corrected C is retrospective reuse of unchanged blind stimuli, not a fresh fully prospective experiment after corrected model freeze. No stimuli or hyperparameters were changed using detector feedback.

All three models have zero threshold crossings on the 48 available pairs. This is conditional stability on selected, already confidently phishing cases; it does not establish robust legitimate behavior or general invariance. RQ3 remains unanswered for a balanced financial-SMS population.

## 18. Statistical tests

Primary paired McNemar comparisons all have p=1 because predictions are identical. On the separate Gateway test, each lexical model versus ModernBERT has 25 discordances in the lexical model's favor, exact p=5.960464e-8; Holm adjustment across three secondary comparisons gives 1.788139e-7. Statistical significance here concerns this selected phishing-only sample and does not overcome source confounding, reviewed-label uncertainty or test-pool reuse.

Rewrite dependence is handled at source-frame level. All exploratory within-frame distance/movement slope intervals include zero: LR 0.00230 [-0.000075, 0.00454], RF 0.01220 [-0.00100, 0.03178], ModernBERT 0.00447 [-0.00492, 0.01947], based on 48 variants and 13 frames with estimable slopes. These descriptive frame-bootstrap intervals are conditional on available approved pairs, not confirmatory association tests. Do not treat 48 variants as 48 independent source messages.

## 19. False positives

All models falsely flag the same sole legitimate held-out message. With no legitimate rewrite variants, no rewrite-induced false-positive rate or recovery claim is supported. The original negative remains a false positive in C0. Observed FPR=100% is a one-control result, not an estimate of a deployment rate. Corrected table 12 and Figure 10 show this denominator.

## 20. Source effects

Gateway contributes 194/228 final representatives and all source-holdout test observations. UCI contributes only one; NUS six; Mendeley 27. Source-level aggregate diversity therefore overstates effective balanced diversity. Personal financial coordination, institutional notifications and malicious gateway captures have different distributions. No dataset group is asserted statistically independent of all others.

## 21. Temporal effects

No temporal performance, drift resistance or newer-message superiority is claimed. Available repository/retrieval dates measure acquisition, and collection metadata may not record when an SMS was sent. Future temporal work needs auditable message timestamps and a prospectively registered cutoff.

## 22. Robustness findings and figures

In the same nine complete phishing frames, mean absolute score changes for C1/C4/C5/C6 are LR 0.00109/0.00105/0.00153/0.00183, RF 0.00167/0.00278/0.00278/0.00167, and ModernBERT 0.00793/0.00703/0.00494/0.00821. These are probability units, not percentages of classification accuracy. ModernBERT's largest complete-core mean is C6 (0.821 percentage points). The largest individual available-pair movement is RF on Mendeley 737, C6: +0.03 (three percentage points), still phishing before and after. Gateway 12309 is a representative trajectory selected by median movement across models among the nine complete frames, not an extreme case. Neither ordering establishes universal contextual superiority or inferiority.

Ten current figures (PNG/SVG) and 16 current CSV tables are under `results/benchmark_v3/corrected_run`. CSV denominators govern interpretation. Original root-level figures remain invalidated historical outputs.

| Figure | Axes/content | Evidence and interpretation |
|---|---|---|
| 1 | Dataset groups versus class counts | Corrected table 01; four nominal groups, nine total controls |
| 2 | Processing stages versus record/family counts | Acquisition and cohort diagnostics; raw scale shrinks sharply after eligibility/review/families |
| 3 | Models versus F1/recall/FPR | Table 04; high F1 coexists with failure on sole control |
| 4 | Actual class versus predicted class | Table 04; TP33/FP1/TN0/FN0 for each model |
| 5 | Models versus held-out-source recall | Tables 05/16; Gateway phishing only, no negative performance |
| 6 | Rewrite conditions versus recall | Table 06; available phishing pairs, denominators vary |
| 7 | Models/conditions versus absolute score movement | Tables 06/10; distinguish available pairs from same-nine-frame core |
| 8 | Models/conditions versus crossing counts | Table 06; zero observed crossings on 48 approved pairs |
| 9 | Linguistic distance versus score movement | Table 09 and paired diagnostics; repeated frames, uncertain slopes |
| 10 | Conditions versus observed control FPR with exact intervals | Table 12; only C0 has one control, all rewrite-condition estimates unavailable |

## 23. Limitations

The benchmark lacks the target control count, independent human annotations and an untouched confirmatory test pool. Source imbalance, possible remaining template relations, reused upstream content, uncertain origin, seven encoding flags and machine-review selection limit external validity. Rewrite quality rejection is selective; only nine phishing frames are complete and no legitimate rewrites survive. Corrected stimulus chronology is retrospective. Probability values are uncalibrated, and one negative makes impressive AUC/F1 especially misleading. ModernBERT was genuinely trained, but a tiny and severely imbalanced training sample is not a fair test of its broad capacity.

## 24. Safe claims

The pipeline acquired multiple sources, enforced source-specific rights and labels, retained provenance, identified a real template leak, preserved the invalidated run and refitted a corrected family-grouped cohort. All three methods used the same primary fitting/test cohort. The contextual classifier was actually fine-tuned. In this selected experiment, all methods misclassified the sole legitimate test control; lexical source-holdout recall exceeded ModernBERT's on the selected Gateway phishing sample. Selected approved phishing rewrites caused no threshold crossings. These are bounded exploratory observations.

## 25. Unsafe claims and next required evidence

Do not claim a successful 300+300 benchmark, independently human-verified ground truth, four independent datasets, newer-message generalization, calibrated risk, balanced robustness, deployment readiness, or contextual models universally better. The next scientific bottleneck is rights-cleared real institutional financial controls with independent human adjudication, sufficient family diversity and a genuinely new frozen test pool. Additional synthetic controls must remain a separate analysis. Scaling model complexity or raw acquisition alone cannot solve the current validity problem.

