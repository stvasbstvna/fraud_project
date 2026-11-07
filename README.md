# Robust Detection of AI-Rewritten Banking Scam Messages

## Project overview

This project studies robustness of banking-smishing detectors. The finalized primary experiment uses SMS only, because mixing SMS and email would confound message channel with authorship. Human/LLM email corpora remain available for a separate extension, but they are not part of the final SMS detector benchmark.

This is a robustness study, not a phishing-generation project. Messages are handled as research data in a controlled environment and are not sent to people or tested against live services.

## Why the topic changed

The project began with a broad combination of SMS and email sources. The finalized version returns to banking smishing and separates the original-message detector benchmark from the later paired AI-rewrite robustness experiment. This avoids calling different text sources “multimodal” and gives the project one reproducible primary dataset.

Smishing-4C is intentionally not used in this project.

## Current research question

> How well do classical text detectors identify banking-related smishing, and how does controlled AI rewriting affect their recall and confidence on the same messages?

## Research gap

Existing work has studied phishing and smishing detection, LLM-based phishing explanations, phishing webpages, and AI-generated phishing mostly as separate problems. However, there is still a gap in testing whether detectors can recognize the same banking scam intent after AI rewrites the message to remove obvious phishing signals and make the message sound more legitimate. This project focuses on that gap by comparing human-written and AI-rewritten banking scam texts and measuring how detection performance changes.

## Planned contribution

The concrete contribution is a provenance-preserving SMS benchmark and evaluation pipeline. It combines SmishX and SmishTank, removes duplicate/template leakage, applies an auditable banking definition, holds banking messages out before training, and compares TF-IDF + Logistic Regression with TF-IDF + Random Forest. A paired AI-rewrite robustness test is the next experimental layer, not a claimed completed result.

The intended benchmark contribution is a paired evaluation: where licensing and provenance allow, each human-written banking scam message will be linked to controlled rewrites that preserve the requested action and scam intent. This design reduces the risk of confusing message topic with authorship.

## Data sources

The final SMS corpus contains 2,117 unique messages after cross-source and within-source deduplication: 1,106 from SmishX and 1,011 from SmishTank. It is split into 1,568 training rows, 392 validation rows, 156 held-out banking-test rows, and one label-quality exclusion. The banking test contains 146 phishing and 10 non-phishing messages. Raw SmishTank data remains outside Git pending confirmation of redistribution terms.

See [data/dataset_inventory.csv](data/dataset_inventory.csv), [data/dataset_collection_plan.md](data/dataset_collection_plan.md), and [resources/links.md](resources/links.md).

## Implemented experiment

1. Normalize SmishX and SmishTank to one SMS schema.
2. Remove exact, canonical, and template duplicates before splitting.
3. Apply the strict banking rule and preserve manual/rule disagreement in an audit table.
4. Hold the banking test set out before model fitting.
5. Split the remaining messages with grouped stratification so template groups cannot cross train and validation.
6. Train TF-IDF + Logistic Regression and TF-IDF + Random Forest.
7. Report accuracy, precision, recall, F1, false-negative rate, ROC-AUC, and confusion counts.

Optional future work may add URL/domain consistency features, but the core benchmark remains text-centered.

## Current results

On validation, Logistic Regression reached F1 = 0.9502 and FNR = 0.0367; Random Forest reached F1 = 0.9186 and FNR = 0.0688. On the held-out banking set, Logistic Regression reached F1 = 0.9697 and FNR = 0.0137. Random Forest reached F1 = 0.9565 and FNR = 0.0205, but classified all 10 legitimate banking controls as phishing. Therefore accuracy alone is not used to choose the detector; Logistic Regression is the primary detector and Random Forest is the comparison model.

The main files are [data/final/sms_master_with_splits.csv](data/final/sms_master_with_splits.csv), [data/final/banking_original_test.csv](data/final/banking_original_test.csv), and [data/review/final_sms_dataset_audit.xlsx](data/review/final_sms_dataset_audit.xlsx).

## Next experiment

- Select only correctly detected phishing rows from the frozen banking test set.
- Produce paired, defanged AI rewrites that preserve intent and requested action.
- Keep detector models and thresholds frozen.
- Measure paired detection-rate change, false-negative-rate change, confidence drop, and attack success rate.
- Treat this as robustness evaluation; do not claim that unchanged baseline scores are a contribution.

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
python src/import_smishtank.py
python src/build_final_sms_dataset.py
python src/train_final_detectors.py
# The audit workbook is already included. Its builder requires @oai/artifact-tool.
```

Python 3.10 or newer is recommended.

## Rewrite experiment dashboard

Build the offline dashboard from the current generation progress and any available paired-evaluation results, then open it locally:

```powershell
python .\src\build_rewrite_dashboard.py
start .\results\rewrite_experiment\dashboard\index.html
```

The dashboard is reporting-only: it does not generate rewrites, call the OpenAI API, retrain detectors, or modify `data/rewrite_experiment/rewrite_pairs.csv`. Metrics remain marked as exploratory until human review is complete.

## Benchmark v2 protocol

Benchmark v1 remains the frozen paired neutral-rewrite pilot; its human review is
handled separately. Benchmark v2 is currently **protocol design only**: no v2 SMS
samples have been generated and no detector has been run on v2. Its purpose is a
larger, scenario-grouped, leakage-resistant test of controlled linguistic
transformations—not to force detector performance to decrease.

Start with [the Benchmark v2 protocol](docs/benchmark_v2_protocol.md), then read
the linked hypotheses, quality rubric, provenance policy, power plan, and
analysis plan. Validate future files (missing files are currently reported as
the expected not-yet-generated state):

```powershell
uv run python .\src\validate_benchmark_v2.py `
  --frames .\data\benchmark_v2\semantic_frames.jsonl `
  --variants .\data\benchmark_v2\variants.jsonl `
  --sources .\data\benchmark_v2\source_manifest.jsonl `
  --config .\configs\benchmark_v2.yaml
```

Use `--strict` in CI once v2 data is required. Final counts are not frozen.
`--phishing-count` and `--legitimate-count` below refer only to unique untouched
confirmatory-final-test scenarios; pilot and quality-validation counts are
separate and provide no confirmatory power credit:

```powershell
uv run python .\src\benchmark_v2_power_analysis.py `
  --baseline-recall 0.95 --expected-recall-difference 0.04 `
  --discordant-pair-rate 0.10 --alpha 0.05 --power 0.80 `
  --phishing-count 500 --legitimate-count 500 --variants-per-scenario 4
```

## Human review of completed rewrites

For the fastest resumable review, launch the local Streamlit application:

```powershell
uv run streamlit run .\src\review_rewrites_app.py
```

Enter a reviewer ID, inspect the original/rewrite pair and deterministic risk
checks, then explicitly choose **Approve**, **Reject**, **Uncertain**, or **Skip**.
Every decision is atomically saved to
`data/rewrite_experiment/human_review/review_decisions.csv`; closing and reopening
the app resumes the fixed randomized order (seed `20260827`). The app never
modifies `rewrite_pairs.csv`, never calls an external API, and never shows
detector predictions or probabilities. Green risk is only a prioritization hint,
not automatic approval.

Validate the saved decisions without changing the source dataset:

```powershell
uv run python .\src\import_rewrite_reviews.py `
  --review-file .\data\rewrite_experiment\human_review\review_decisions.csv `
  --dry-run
```

After all 153 completed rows have an explicit decision and dry-run succeeds,
perform the validated import:

```powershell
uv run python .\src\import_rewrite_reviews.py `
  --review-file .\data\rewrite_experiment\human_review\review_decisions.csv
```

The final import verifies the original/rewrite hashes, recomputes the approval
rule, creates a timestamped backup and audit CSV, and atomically replaces only
the source CSV after every validation passes. Use `--allow-incomplete` only for
an explicitly non-final partial import.

The Excel workflow remains available when a spreadsheet is preferable.

Export a blinded, deterministically randomized workbook containing only completed neutral rewrites:

```powershell
python .\src\export_rewrite_review_workbook.py
```

Review every row in `data/rewrite_experiment/human_review/rewrite_human_review.xlsx`, save the workbook, and validate it without changing the source CSV:

```powershell
python .\src\import_rewrite_reviews.py --review-file .\data\rewrite_experiment\human_review\rewrite_human_review.xlsx --dry-run
```

After the dry run succeeds, import the decisions atomically. The importer creates a timestamped backup and audit CSV:

```powershell
python .\src\import_rewrite_reviews.py --review-file .\data\rewrite_experiment\human_review\rewrite_human_review.xlsx
```

Final evaluation includes only rows whose enforced human-review status is `approved`. Generator self-reports remain in their original columns and are not treated as human judgments.
