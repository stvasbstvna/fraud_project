# Experiment Plan

## Primary hypothesis

For scam messages with the same banking intent, the baseline detector's false-negative rate will be higher on reviewed AI rewrites than on human-written source messages.

## Design

The primary test set contains source/rewrite pairs linked by `pair_id`. All members of a pair and near-duplicate family stay in one split. The main analysis compares paired binary outcomes and reports bootstrap confidence intervals clustered by pair. Unpaired AI-written messages are a secondary, clearly labeled analysis.

## Model groups

1. TF-IDF + Logistic Regression (required baseline).
2. Random Forest or XGBoost if time allows.
3. DistilBERT if time and compute allow.
4. LLM-as-judge on a small manually reviewed sample.
5. Optional future URL/domain consistency model.

## Metrics

- Accuracy, precision, recall, and F1-score.
- False-negative rate (primary harm metric).
- Absolute and relative performance drop from human-written to AI-rewritten messages.
- Counts and confidence intervals, reported overall and by channel.

The positive class is `phishing_scam`. Thresholds are chosen on validation data and then frozen.

## Conditions

| ID | Training | Features/model | Test purpose |
|---|---|---|---|
| B1 | human + legitimate | TF-IDF + LR | clean baseline |
| B2 | same as B1 | RF/XGBoost optional | classical comparison |
| B3 | same as B1 | DistilBERT optional | transformer comparison |
| R1 | B1 model | paired human vs rewrite | primary detection gap |
| M1 | human + approved training rewrites | TF-IDF + LR | augmentation mitigation |
| M2 | M1 data | text + action/intent features | intent mitigation |
| M3 | frozen subset | baseline + LLM review | exploratory hybrid mitigation |

## Robustness checks

- Channel-stratified results.
- Dataset/source-held-out results when sample size permits.
- Generator-held-out rewrites when multiple generators are available.
- Near-duplicate audit and prompt-template artifact analysis.
- Equal-size paired subset so class/source counts cannot explain the gap.

## Mitigation comparison

Mitigations use the same held-out test pairs and report the change in false-negative rate relative to B1. Training augmentation may include only training-split rewrites. The LLM judge receives a fixed rubric and redacted text; human labels remain the reference.

## Stop conditions

Do not report a final banking benchmark if licensing, provenance, or annotation quality remains unresolved. Do not pool channels when a subgroup is too small to support interpretable results.
