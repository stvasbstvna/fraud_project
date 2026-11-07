# Dataset Files

This directory contains the original broad text collection and the finalized SMS-only detector benchmark.

## Processed outputs

| File | Purpose | Rows |
|---|---|---:|
| `processed/unified_text_messages.csv` | all committed standardized messages | 11,186 |
| `processed/smishtank_normalized.csv` | normalized SmishTank messages; local/reproducible source output | 1,054 |
| `processed/banking_candidates.csv` | exact keyword/phrase matches | 6,372 |
| `processed/banking_manual_review.csv` | candidate review queue with blank manual decisions | 6,372 |
| `processed/banking_human_written.csv` | source-supported human-written candidates | 1,914 |
| `processed/banking_ai_generated.csv` | source-supported AI-generated candidates | 4,285 |
| `processed/banking_ai_rewritten.csv` | license-cleared AI rewrites | 0 (header only) |

The older `processed/banking_*` files are broad keyword-candidate artifacts and are not the final experimental dataset.

## Final SMS benchmark

| File | Purpose | Rows |
|---|---|---:|
| `final/sms_master_with_splits.csv` | complete deduplicated corpus with frozen split and provenance | 2,117 |
| `final/train_sms.csv` | detector training set | 1,568 |
| `final/validation_sms.csv` | grouped validation set | 392 |
| `final/banking_original_test.csv` | held-out original banking SMS test set | 156 |
| `final/banking_decision_audit.csv` | strict-rule and prior-review decision trail | 2,117 |
| `final/dataset_summary.csv` | counts used in the report/workbook | 23 |

The primary corpus uses SMS only: SmishX and SmishTank. Cross-model email data is intentionally excluded from this experiment. Banking means an explicit bank/card/payment-service brand or explicit bank/card-account context; generic account, OTP, payment, crypto, and promotion language alone are insufficient.

## Documentation

- `dataset_inventory.csv`: every uploaded or linked dataset/resource, exact shapes, licensing, and commit decision.
- `dataset_source_details.md`: audit findings, per-sheet workbook counts, labels, authorship, and processed totals.
- `dataset_schema.md`: definitions for all standardized and manual-review columns.
- `dataset_collection_plan.md`: acquisition, licensing, reproduction, and future-integration steps.
- `banking_filtering_plan.md`: exact filter list, current counts, and manual annotation procedure.
- `ATTRIBUTION.md`: licenses, citations, repository versions, and provenance for committed rows.

## Safety and provenance

URLs in committed message text and the `url` column are defanged; email addresses and phone-like identifiers are redacted. Raw source archives remain outside Git. The processed CSVs contain research examples of phishing and spam; do not visit destinations, send messages, or use the content for targeting.

Rebuild the final benchmark with:

```bash
python src/import_smishtank.py
python src/build_final_sms_dataset.py
python src/train_final_detectors.py
# The audit workbook is already included. Its builder requires @oai/artifact-tool.
```

The generated audit workbook is `review/final_sms_dataset_audit.xlsx`. Raw source archives remain outside Git.
