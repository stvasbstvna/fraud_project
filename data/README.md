# Dataset Files

This directory now contains actual standardized, license-cleared message rows rather than empty placeholders.

## Processed outputs

| File | Purpose | Rows |
|---|---|---:|
| `processed/unified_text_messages.csv` | all committed standardized messages | 11,186 |
| `processed/banking_candidates.csv` | exact keyword/phrase matches | 6,372 |
| `processed/banking_manual_review.csv` | candidate review queue with blank manual decisions | 6,372 |
| `processed/banking_human_written.csv` | source-supported human-written candidates | 1,914 |
| `processed/banking_ai_generated.csv` | source-supported AI-generated candidates | 4,285 |
| `processed/banking_ai_rewritten.csv` | license-cleared AI rewrites | 0 (header only) |

The word “banking” in these filenames means keyword candidate until `manual_banking_related` has been reviewed. No final banking-filtered dataset is claimed.

## Documentation

- `dataset_inventory.csv`: every uploaded or linked dataset/resource, exact shapes, licensing, and commit decision.
- `dataset_source_details.md`: audit findings, per-sheet workbook counts, labels, authorship, and processed totals.
- `dataset_schema.md`: definitions for all standardized and manual-review columns.
- `dataset_collection_plan.md`: acquisition, licensing, reproduction, and future-integration steps.
- `banking_filtering_plan.md`: exact filter list, current counts, and manual annotation procedure.
- `ATTRIBUTION.md`: licenses, citations, repository versions, and provenance for committed rows.

## Safety and provenance

URLs in committed message text and the `url` column are defanged; email addresses and phone-like identifiers are redacted. Raw source archives remain outside Git. The processed CSVs contain research examples of phishing and spam; do not visit destinations, send messages, or use the content for targeting.

Rebuild the six outputs with `python -m src.build_dataset_files` and the three source paths described in `dataset_collection_plan.md`.
