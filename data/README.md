# Data Directory

This repository does not redistribute raw scam-message datasets. Place approved downloads in the ignored subdirectories and record provenance in `dataset_inventory.csv`.

```text
raw/        unchanged source files
processed/  normalized, redacted records and audit files
generated/  controlled AI rewrites with prompt logs
final/      frozen benchmark splits and dataset card
```

Expected normalized columns are defined in `dataset_collection_plan.md`. Every final artifact should have a checksum, creation command, source version, exclusion log, and license note. A file in `raw/` is not automatically approved for publication or model use.

The uploaded `research.zip` was inspected outside the repository. It contains PDFs, two copies of an AI-generated email CSV, a nested workbook archive, and a licensed cross-model research package. None of those raw files has been copied here.
