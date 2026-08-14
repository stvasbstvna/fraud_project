# Robust Detection of AI-Rewritten Banking Scam Messages

## Project overview

This project studies whether AI-written or AI-rewritten banking scam messages can bypass phishing detectors more effectively than human-written scam messages. The focus is text-based banking phishing across SMS, email, and similar message channels. The goal is to compare detector performance on human-written and AI-rewritten scam messages, measure the detection gap, and test mitigation strategies such as data augmentation, intent/action features, and hybrid LLM-assisted detection.

This is a robustness study, not a phishing-generation project. Messages are handled as research data in a controlled environment and are not sent to people or tested against live services.

## Why the topic changed

The project began as a banking-smishing study. After reviewing newer work on LLM-generated phishing emails, adversarial phishing evaluation, and explainable SMS detection, I narrowed the gap differently. The more useful question is not limited to SMS or to adding URL features. It is whether the same banking scam intent becomes harder to detect after an AI system rewrites the wording to sound more ordinary and trustworthy. SMS remains one channel, but email and other text-message formats are now part of the study.

Smishing-4C is intentionally not used in this project.

## Current research question

> How does prompt-based adversarial rewriting affect phishing detector robustness on confirmed banking-related phishing messages?

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

The repository contains 11,186 standardized messages and 6,372 banking keyword candidates from license-cleared sources. The baseline and manually reviewed pilot results are documented in the prompt-attack plan. The next experimental artifact is a 30-50-row base set selected from the 91 confirmed banking-phishing rows described in the research notes. That reviewed source file is not committed yet, so the prompt-attack CSV files contain validated schemas rather than fabricated rows.

See [docs/prompt_attack_master_plan.md](docs/prompt_attack_master_plan.md) for the complete literature review, P0-P7 taxonomy, dataset design, metrics, slide text, Overleaf sections, and execution plan. The experiment schemas are under [data/prompt_attack/](data/prompt_attack/).

## Next steps

- Add the reviewed `confirmed_banking_phishing_only.csv` as an analysis-only local input.
- Select 30-50 correctly detected, confirmed banking-phishing rows.
- Freeze prompt IDs, detector preprocessing, vocabulary, and threshold.
- Create or import only safe, licensed/approved P0-P7 variants.
- Run the paired robustness evaluation and fill the ASR result table.

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
