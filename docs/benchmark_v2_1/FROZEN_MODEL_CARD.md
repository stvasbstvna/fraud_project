# Frozen detector card

Actual joblib pipelines were loaded read-only by `python -m src.benchmark_v2_1.audit_runtime`. No prediction or fit was called. Full actual parameter extraction, class arrays, vocabulary/IDF hashes and current data-file hash are in `results/benchmark_v2_1/diagnostics/runtime_audit.json`.

| Property | Logistic Regression | Random Forest |
|---|---|---|
| File | `models/final/tfidf_logistic_regression.joblib` | `models/final/tfidf_random_forest.joblib` |
| SHA-256 | `84ba84863ce9a8fd757cd4e9babc6dacf39496223299a06df0054f94ca688fcc` | `99c4a06e7ad52ff000c0a1d8818ca61cdc268d929a1a970e79d74b6e0c38b4fc` |
| Actual vocabulary size | 3,715 | 3,715 |
| Feature cap | 50,000 | 20,000 |
| Class labels | `[0, 1]` | `[0, 1]` |
| Classifier | C=1, lbfgs, balanced, max_iter=2000 | 400 trees, min_samples_leaf=2, sqrt features, balanced_subsample |
| Random state | 42 | 42 |
| Fixed decision threshold | 0.5 | 0.5 |

Both fitted vectorizers: word unigrams/bigrams `(1,2)`, English stop words, lowercase, min_df=2, max_df=0.95, sublinear_tf=True, L2 normalization, smooth/use IDF=True. Actual vocabulary hash is `04ebf4323cea101955ab57b47e6d4078de558259cb67b60e548f6bf1a186ab3b` for both; IDF bytes hash `75c552b07dca4e0e197f76dbec293455d166d38e50dc36aef0acf2669c25046a` for both. The distinct vectorizers happen to have identical fitted vocabulary/IDF on these data; differing feature caps do not by themselves prove different fitted spaces. This corrects an inference in the older representation documentation without changing that historical file.

Training metadata (`results/final_detectors/run_metadata.json`) identifies `data/final/sms_master_with_splits.csv`, train split only, 1,568 rows. Current full data hash: `2cb3e227278d5fd06ba2671036b68489cfcad1a28d10040624f0187fec4ccf73`. That current hash and matching saved models do not prove the exact bytes present at original training time; no historical training-input hash is inferred. Current train row count and membership are separately inspectable. Exclude training and template overlaps for any external robustness source. Never refit vocabulary, calibrate, tune thresholds, or train on C1–C6 before confirmatory evaluation.

`evaluate` verifies the model and frozen dataset/config hashes, finds probability column by class value 1, then calls only transform/predict/predict_proba. For exact 0.5 ties, retain the saved pipeline's `predict` behavior rather than invent a different tie rule.
