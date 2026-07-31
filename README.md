# Robust Detection of AI-Rewritten Banking Scam Messages

## Project overview

This project studies whether AI-written or AI-rewritten banking scam messages can bypass phishing detectors more effectively than human-written scam messages. The focus is text-based banking phishing across SMS, email, and similar message channels. The goal is to compare detector performance on human-written and AI-rewritten scam messages, measure the detection gap, and test mitigation strategies such as data augmentation, intent/action features, and hybrid LLM-assisted detection.

This is a robustness study, not a phishing-generation project. Messages are handled as research data in a controlled environment and are not sent to people or tested against live services.

## Why the topic changed

The project began as a banking-smishing study. After reviewing newer work on LLM-generated phishing emails, adversarial phishing evaluation, and explainable SMS detection, I narrowed the gap differently. The more useful question is not limited to SMS or to adding URL features. It is whether the same banking scam intent becomes harder to detect after an AI system rewrites the wording to sound more ordinary and trustworthy. SMS remains one channel, but email and other text-message formats are now part of the study.

Smishing-4C is intentionally not used in this project.

## Final research question

> Can AI-rewritten banking scam messages bypass phishing detectors more effectively than human-written scam messages, and what mitigation strategies can reduce this detection gap?

## Research gap

Existing work has studied phishing and smishing detection, LLM-based phishing explanations, phishing webpages, and AI-generated phishing mostly as separate problems. However, there is still a gap in testing whether detectors can recognize the same banking scam intent after AI rewrites the message to remove obvious phishing signals and make the message sound more legitimate. This project focuses on that gap by comparing human-written and AI-rewritten banking scam texts and measuring how detection performance changes.

## Planned contribution

This project contributes a structured benchmark plan for evaluating phishing detector robustness against AI-rewritten banking scam messages. It organizes public resources and datasets, separates human-written and AI-generated or AI-rewritten content, filters for banking-related scam intent, compares baseline phishing detectors, and proposes mitigation strategies to reduce false negatives.

The intended benchmark contribution is a paired evaluation: where licensing and provenance allow, each human-written banking scam message will be linked to controlled rewrites that preserve the requested action and scam intent. This design reduces the risk of confusing message topic with authorship.

## Data sources

The current source inventory includes SmishTank, the SmishX relabeled SMS data, PhishFuzzer email data, an uploaded AI-generated phishing/legitimate email CSV, an uploaded bank-transaction SMS workbook, and an uploaded cross-model human/LLM phishing package. No final banking-filtered dataset has been created yet. Raw data is not tracked until its redistribution rights and safety requirements are checked.

See [data/dataset_inventory.csv](data/dataset_inventory.csv), [data/dataset_collection_plan.md](data/dataset_collection_plan.md), and [resources/links.md](resources/links.md).

## Planned experiments

1. Create a deduplicated, provenance-preserving common schema.
2. Apply a banking candidate filter and manually audit a stratified sample.
3. Train TF-IDF + Logistic Regression as the primary baseline.
4. Add Random Forest or XGBoost if time allows, and DistilBERT if resources allow.
5. Compare performance on human-written scam messages and their AI rewrites using accuracy, precision, recall, F1, false-negative rate, and the paired performance drop.
6. Test mitigation through rewrite-aware augmentation, intent/action features, and a small hybrid LLM-assisted review condition.
7. Use an LLM as judge only on a small, manually checked sample; it is not treated as ground truth.

Optional future work may add URL/domain consistency features, but the core benchmark remains text-centered.

## Current stage

The repository structure, research question, source inventory, study protocol, and starter processing code are in place. The uploaded materials have been inventoried, but no raw archive or large dataset has been committed. Dataset licensing, banking-label validation, paired rewrite generation, and experiments remain pending.

## Next steps

- Confirm licenses and access terms for each candidate dataset.
- Inspect and de-duplicate the uploaded email CSV and bank-transaction workbook locally.
- Define the human annotation guide and test inter-annotator agreement on a pilot sample.
- Freeze a leakage-safe split before generating rewrites.
- Run the baseline and then the paired robustness evaluation.

## Repository guide

- `research_question.md` and `project_plan.md`: scope, gap, contribution, milestones, limitations, and future work.
- `literature/`: reading list, matrix, resource synthesis, and notes.
- `resources/`: threat context and external repositories/tools.
- `data/`: inventory, collection/filtering plan, schema, and untracked data directories.
- `src/`: starter preprocessing, filtering, feature, training, and evaluation modules.
- `notebooks/`: numbered analysis workflow placeholders.
- `prompts/`: controlled research prompts and an empty audit log.
- `experiments/`: preregistered experiment plan and empty result schemas.
- `paper/` and `slides/`: writing and mentor-update outlines.

## Setup

```bash
python -m venv .venv
python -m pip install -r requirements.txt
python -m src.preprocessing --help
python -m src.banking_filter --help
```

Python 3.10 or newer is recommended.
