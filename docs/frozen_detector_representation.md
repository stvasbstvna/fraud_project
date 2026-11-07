# Frozen detector representation

This record was extracted read-only from the two joblib pipelines in `models/final/`. No `fit`, prediction, calibration, or detector evaluation was performed.

## Shared TF–IDF settings

| Parameter | Logistic Regression pipeline | Random Forest pipeline |
|---|---|---|
| analyzer | `word` | `word` |
| ngram range | `(1, 2)` | `(1, 2)` |
| lowercase | `true` | `true` |
| min_df | `2` | `2` |
| max_df | `0.95` | `0.95` |
| sublinear_tf | `true` | `true` |
| max_features | `50,000` | `20,000` |
| stop_words | scikit-learn `english` | scikit-learn `english` |
| tokenizer | `null` (default analyzer tokenization) | `null` |
| token pattern | `(?u)\b\w\w+\b` | `(?u)\b\w\w+\b` |
| preprocessor | `null` | `null` |
| strip accents | `null` | `null` |
| TF–IDF norm | L2 | L2 |
| use/smooth IDF | `true` / `true` | `true` / `true` |
| dtype | NumPy float64 | NumPy float64 |

With scikit-learn's fitted vocabulary and IDF values, each document is lowercased, tokenized into word unigrams and bigrams, English stop words are removed, sublinear term frequency uses `1 + log(tf)` for nonzero counts, smoothed IDF is applied, and the resulting vector is L2-normalized. The two pipelines have different feature caps and separately fitted vectorizers; their feature spaces must not be treated as identical.

## Classifiers

### TF–IDF + Logistic Regression

- `C=1.0`, solver `lbfgs`, intercept enabled;
- `class_weight="balanced"`;
- `max_iter=2000`, `random_state=42`.

For its actual frozen feature vector `x`, binary logistic probability is `1 / (1 + exp(-(wᵀx + b)))`. This does not imply calibration outside the training distribution.

### TF–IDF + Random Forest

- 400 trees, Gini splits, bootstrap sampling;
- `max_features="sqrt"`, `min_samples_leaf=2`;
- `class_weight="balanced_subsample"`;
- `n_jobs=-1`, `random_state=42`.

The reported class probability is the mean of tree-level class probability estimates for the frozen forest.

## Integrity identifiers

- Logistic Regression pipeline SHA-256: `84ba84863ce9a8fd757cd4e9babc6dacf39496223299a06df0054f94ca688fcc`
- Random Forest pipeline SHA-256: `99c4a06e7ad52ff000c0a1d8818ca61cdc268d929a1a970e79d74b6e0c38b4fc`

These artifacts remain Benchmark v1/frozen detector inputs. Benchmark v2 or v2.1 must never refit their vectorizers or classifiers.
