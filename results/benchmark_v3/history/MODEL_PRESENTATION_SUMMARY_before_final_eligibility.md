# Model presentation summary: corrected exploratory v3

The current models/results are in `models/benchmark_v3/corrected_run` and `results/benchmark_v3/corrected_run`. Original artifacts are preserved but invalidated after template leakage. All current comparisons remain exploratory because the test pool had already been inspected before correction.

| Model | Plain-language description | Actual fitting |
|---|---|---|
| Logistic Regression | Uses TF-IDF word-pattern features with a linear decision rule | Corrected training cohort; fixed hyperparameters |
| Random Forest | Uses the same TF-IDF representation with nonlinear tree decisions | Same corrected training cohort; fixed hyperparameters |
| ModernBERT-base | Uses a context-sensitive Transformer representation and an explicitly trained binary classification head | Full 149,606,402-parameter CPU fine-tuning, two epochs, same cohort |

ModernBERT is `answerdotai/ModernBERT-base`, revision `8949b909ec900327062f0ebf497f51aef5e6f0c8`. It was not replaced, used as fill-mask, or left with an untrained classifier. CPU feasibility and real model tests passed. Seed 42, fixed optimizer/training configuration and maximum length 128 were retained for corrected fits. Best checkpoint used validation loss only: primary epoch 1, separate source fit epoch 2. No held-out score selected hyperparameters. Manifests record hashes, tokenizer, source checkpoint and environment. Scores are not independently calibrated.

Primary train/validation/test: 160/34/34. The test contains 33 phishing and ONE legitimate message. Every model predicted phishing for all 34.

| Primary metric | LR | RF | ModernBERT |
|---|---:|---:|---:|
| Accuracy | 0.970588 | 0.970588 | 0.970588 |
| Precision | 0.970588 | 0.970588 | 0.970588 |
| Recall | 1 | 1 | 1 |
| F1 | 0.985075 | 0.985075 | 0.985075 |
| Specificity | 0 | 0 | 0 |
| False-negative rate | 0 | 0 | 0 |
| False-positive rate | 1/1 | 1/1 | 1/1 |
| ROC-AUC / PR-AUC | 1 / 1 | 1 / 1 | 1 / 1 |

A constant-phishing classifier has identical threshold metrics. AUC=1 reflects ranking against just one negative and does not establish good banking discrimination. Exact 95% FPR interval is [0.025, 1]; recall interval [0.8942, 1]. Primary paired McNemar tests all have p=1. High F1 masks zero specificity in this highly imbalanced sample.

The separate source experiment fits new models on 29 train/five validation messages and tests 194 Gateway phishing messages: LR and RF recall 194/194=1; ModernBERT 169/194=0.871134 (25 misses). The 25 paired discordances give exact p=5.960464e-8, Holm-adjusted 1.788139e-7 across three secondary comparisons. No legitimate source-test controls means specificity/FPR/discrimination AUC are unavailable. This selected source effect does not prove that lexical representations are causally superior. Temporal evaluation was not run.

The balanced primary rewrite experiment was not run because controls were insufficient. An exploratory supplement scores 48 approved phishing variants and 34 originals (82 rows/model), with no legitimate rewrites and selective quality attrition. All models show zero threshold crossings on the 48 pairs. In the same nine complete phishing frames, largest condition mean absolute changes are LR C6=0.001825, RF C4/C5=0.002778, ModernBERT C6=0.008206. Largest individual available change is RF +0.03 on Mendeley 737 C6, still phishing. Distance/movement slope intervals all include zero. These results do not establish broad semantic robustness; corrected analysis retrospectively reuses unchanged blind stimuli generated before corrected refitting.

Current figures 3–5 show detection/confusion/source recall; 6–9 show conditional rewrite behavior; figure 10 shows the sole legitimate control being falsely flagged by every model. Sixteen CSV tables retain exact denominators. Consult `docs/benchmark_v3/FINAL_REPORT.md` and the final verification receipt for complete limitations and test results.

Supported conclusion: contextual classification was technically implemented and trained, but this small, source-skewed experiment cannot establish superior real financial-SMS discrimination or robustness. The next need is more independently reviewed real legitimate controls and a new untouched test pool.
