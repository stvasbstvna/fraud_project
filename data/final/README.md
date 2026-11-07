# Frozen SMS benchmark

This directory is the single source of truth for the primary detector experiment.

- `sms_master_with_splits.csv`: every retained row, provenance, banking decision, template group, and split.
- `train_sms.csv`: training data only.
- `validation_sms.csv`: grouped validation data only.
- `banking_original_test.csv`: untouched original banking SMS used for final evaluation.
- `banking_decision_audit.csv`: rule/manual decision provenance and conflicts.
- `dataset_summary.csv`: exact counts for tables and slides.

The split was made after removing exact/canonical duplicates and grouping template-like messages. No template group overlaps train, validation, or banking test. The held-out banking set must not be used to fit vocabulary, tune models, or choose thresholds.

The one `excluded_label_quality` row is preserved for audit but excluded from all detector evaluation because its text is an anti-smishing warning while its source label is phishing.
