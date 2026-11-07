# Benchmark v3 final research report

Status: **COMPLETED_EXPLORATORY; BALANCED_TARGET_UNMET; PRIMARY_C_NOT_RUN**. Authoritative paths are `data/benchmark_v3/final_run`, `models/benchmark_v3/final_run` and `results/benchmark_v3/final_run`. Original and intermediate runs are preserved and superseded.

The strongest finding is that high F1 coexists with failure on the sole legitimate test control. This is a validity limitation, not demonstrated useful financial-SMS discrimination.

## 1. Data acquisition

Eight source groups supplied 234,547 raw records. Heuristic English screening retained 209,827 candidates; financial screening retained 37,063. Exact duplicate excess was 13,625, leaving 23,438 unique financial candidates and 12,247 rights-eligible candidates. Screening is not semantic validation. Sting9 supplied zero rows: actual 401 export responses, 404 documented dump and conflicting license statements are preserved in STING9_ACCESS_AND_LICENSE_AUDIT.md.

## 2. Source provenance

Final source counts: Gateway 167, Mendeley 24, NUS 4. These are nominal dataset groups, not independent populations. Original row IDs, original annotations, duplicate origins and reviewed labels remain distinct. Origin accounting is 28 real-source observations, 167 uncertain-origin observations and zero synthetic observations. Real-source does not establish authenticated bank authorship.

## 3. License findings

SOURCE_LICENSE_AUDIT.md and provenance/upstream_rights_evidence.json retain original evidence. Mendeley and UCI state CC BY 4.0; Gateway releases repository data under MIT. NUS authors declare copyright-free unlimited use, which is not an invented CC0 grant. SmishTank, SpamHunter, Super SMS and ExAIS remain excluded from modeling for unresolved reuse evidence. Aggregator availability does not replace original rights.

## 4. Label harmonization

Canonical decisions distinguish phishing, legitimate, uncertain and exclusion. Spam was not automatically phishing; ham was not automatically a legitimate banking notification. These are automated semantic judgments, not independent human ground truth. Source reviewers A/B and adjudicator use exact model snapshots, raw response hashes and confidence gates; confidence is not calibrated label accuracy.

## 5. Financial and English eligibility

707 source candidates received fresh v3.1 review; 314 initially passed and two policy exclusions left 312. Conservative family grouping and two further coordination exclusions produced an intermediate 228-family cohort. A subsequent detector-blind eligibility audit reviewed ALL 228 representatives: 195 retained, 33 phishing candidates excluded for language/context, no labels flipped. All nine legitimate controls survived. ASCII screening alone had admitted non-English messages. The final audit used 26 actual A/B/J requests; all decisions and raw evidence are bound in final_eligibility_audit. This post-score population correction makes final inference exploratory.

## 6. Defanging

Typed URL, phone, email, account and transaction placeholders remove operational destinations. Date/time handling avoids ordinary date-as-phone errors. Amounts and ordinary financial language remain. Upstream encoding flags are disclosed, with no post-score text repair. No private inbox data was accessed.

## 7. Exact duplicate removal

13,625 duplicate excess financial records were removed from representative selection while retaining their origins. Exact uniqueness alone is not independence. Rights-aware representative selection precedes modeling.

## 8. Template families

A genuine Shijo/Sinco payee-registration train/test template leak invalidated the original 231-family run. Its artifacts remain preserved. Broader source-only normalization fixed the known optional-suffix pattern. The intermediate corrected_run was later superseded by final English/financial eligibility. Only final_run supplies current results; undetected semantic dependencies remain possible.

## 9. Final sample

195 family representatives: 186 phishing and nine legitimate; 28 real-source, 167 uncertain-origin, zero synthetic. The desired 300+300 target is NOT MET. Acquisition volume cannot substitute for rights-cleared and policy-valid controls.

## 10. Splits

Primary train/validation/test: 137/29/29, with phishing/legitimate counts 130/7, 28/1 and 28/1. Separate source experiment: train 24 (16/8), validation four (3/1), test 167 Gateway phishing messages. All three methods share each experiment’s cohort. The earlier test pool was inspected before correction; this is not an untouched confirmatory holdout.

## 11. Leakage and integrity

The final verifier reconstructs source approvals, full eligibility coverage, exact/family isolation, pooled-origin source exclusion, train-only TF-IDF, frozen model hashes, detector-blind payloads, cached predictions and paired deltas. 1,044 historical files remain unchanged. Protocol, correction plan, eligibility plan/decision and cohort hashes bind the final freeze. No rewrite enters model fitting.

## 12. Logistic Regression

Actual separate primary and source fits use fixed TF-IDF and Logistic Regression settings with threshold 0.5. Primary model SHA-256: df89f5e2b629b09f3e3f9fe2b6830726bd2d9eb17e5e51f3cdbf8f8a2dedb7bf. TF-IDF has 2,303 primary features and 779 source-fit features, fitted only on training rows.

## 13. Random Forest

Actual separate primary and source fits use the same fitted TF-IDF representation as LR and unchanged tree settings. Primary model SHA-256: 19be45a63832fa8670849a824db84ba37b9fe7b405ae9a7df7776d5aa8147bb7. No test-based hyperparameter selection was introduced.

## 14. ModernBERT

Actual full-parameter CPU fine-tuning used answerdotai/ModernBERT-base revision 8949b909ec900327062f0ebf497f51aef5e6f0c8 with an explicit binary classifier: 149,606,402 parameters, two epochs, AdamW learning rate 2e-5, batch two, weight decay 0.01, seed 42, max length 128. Validation cross entropy selected primary epoch one (0.1226553) and source epoch two (0.2727128). Primary weights SHA-256 7ea2311d32ef766a51e3ccc25046f81c8bcdf80d6e3c07b3e42140822af25d43; source weights a847ce948802af28ba90999b5b9ffe01a20b1eafeee66477c570dcbfcd36877e. No fill-mask substitution, frozen-encoder shortcut or independent probability calibration. Dedicated environment and real feasibility evidence are retained.

## 15. Experiment A: original detection

All models predict phishing on all 29 test messages: TP28, FP1, TN0, FN0. Accuracy/precision 0.965517; recall 1; F1 0.982456; specificity zero; FPR 1/1. Constant-phishing yields identical threshold metrics. ROC/PR AUC approximately one compares against only one negative and does not establish reliable discrimination. Exact 95% recall interval [0.876564,1]; FPR [0.025,1].

## 16. Experiment B: source generalization

On 167 selected Gateway phishing messages, separately trained LR and RF detect 167/167; ModernBERT detects 147/167, recall 0.880240, 20 false negatives. No FPR, specificity or discrimination AUC can be estimated from this single-class test. Source-label composition confounds interpretation; this is not universal lexical superiority.

## 17. Experiment C: linguistic robustness

Balanced primary C was NOT RUN: the predeclared minimum ten legitimate controls was unmet. Original blind generation used 35 sources, 140 initial variants and 30 permitted quality retries. 51 variants passed review; 89 initial condition slots remained rejected/unresolved. One adjudication batch returned wrong IDs; its 20 decisions were excluded. Final unchanged-stimulus held-out intersection contains 28 originals (27 phishing/one legitimate) and 39 approved phishing rewrites: 67 scored rows/model. C1/C4/C5/C6 paired counts are 8/11/10/10. Seven phishing frames have all four conditions; no legitimate rewrite survives. Stimuli were generated after original model freezing but before final refitting: retrospective detector-blind reuse, not a fresh prospective final-model experiment.

## 18. Statistics

Primary paired McNemar comparisons all have p=1. Source comparisons LR/ModernBERT and RF/ModernBERT each have 20 discordances, exact p=1.9073486328125e-6, Holm secondary-family p=5.7220458984375e-6. These selected-source tests do not remove label uncertainty or retrospective correction. Frame-bootstrap distance/movement slopes on 11 estimable phishing frames: LR 0.00351666 [0.00082607,0.00621474]; RF 0.00579903 [-0.00878161,0.02025099]; ModernBERT 0.00114436 [-0.00078948,0.00341799]. Even the LR interval excluding zero is descriptive, selected and noncausal, not a confirmatory result.

## 19. False positives

All models falsely flag the sole legitimate test control already at C0. No legitimate variants exist, so rewrite-induced false-positive behavior is unavailable. Observed FPR 100% is a one-control observation, not a deployment estimate.

## 20. Source effects

Gateway supplies 167/195 final representatives and the entire source test. Mendeley supplies 24 and NUS four. Source count is not balanced diversity, source origin is not independent provenance, and this composition cannot characterize the general financial-SMS population.

## 21. Temporal effects

Temporal evaluation NOT RUN. Collection/repository/retrieval timestamps do not reliably establish SMS sending dates. No newer-message performance, temporal robustness or drift claim is supported.

## 22. Robustness observations and figures

All models show zero threshold crossings on 39 approved pairs. Largest individual absolute change: RF Mendeley737 C6, 0.985 to 1.0 (+0.015 probability, 1.5 percentage points), still phishing. Representative complete-frame trajectory is Mendeley379, selected by median movement across models. Seven-frame complete-core maximum condition mean absolute changes: LR C6 0.00193184; RF C5 0.00285714; ModernBERT C6 0.000813254. Ten PNG/SVG figures and 16 CSV/Markdown tables are in results/benchmark_v3/final_run. Figures 1–2 show source/class composition and attrition; 3–5 detection/confusion/source recall; 6–9 paired recall, movement, crossings and distance; 10 the sole control’s false positive. Unequal surviving conditions and missing legitimate variants prevent a balanced robustness conclusion.

## 23. Limitations

Nine legitimate training-population controls, one legitimate test control, machine labels, uncertain source origins, possible template dependence, source imbalance, reused test pool, post-score eligibility correction and selective rewrite attrition limit inference. Seven complete phishing trajectories are not seven representative trajectories of both classes. Tiny imbalanced training data cannot fairly establish ModernBERT’s broad capacity. No deployment recommendation follows.

## 24. Safe claims

Multiple sources were acquired with source-specific rights/provenance controls; a real template leak and eligibility errors were preserved and corrected through separate freezes and actual refits. Three models were actually trained, including full ModernBERT. The final selected sample shows identical primary threshold decisions, source-specific recall differences and no crossings among approved phishing rewrites. All are exploratory observations.

## 25. Unsafe claims and next evidence

Do not claim 300+300 completion, independent human/expert ground truth, balanced robustness, untouched confirmatory testing, newer-message generalization, calibrated risk or universal superiority. Next required evidence is rights-cleared real institutional legitimate controls, independent human adjudication, family diversity and a genuinely new frozen test set. No commit, push, publication, private messaging or Sting9 redistribution occurred.

## Verification

Fresh repository suite: **257 passed, 1 skipped in 7.50s**; dedicated ModernBERT suite: **20 passed in 4.98s**. Torch is absent from the original environment, accounting for the skip. `python -m src.benchmark_v3.verify --final` checks actual raw evidence and frozen artifacts. Total actual requests: 246 (189 source, 31 rewrite, 26 final eligibility); recorded usage 523,783 input/226,609 output tokens. The 85 invalid-instrument source calls are preserved, not counted as valid labels. See TEST_RESULTS.md, RUNBOOK.md and final_run/verification.json.
