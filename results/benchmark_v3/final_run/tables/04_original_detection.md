# 04 original detection

Exploratory machine-reviewed research; see exact denominators and limitations in FINAL_REPORT.md. CSV is authoritative; preview limited to30rows.

| model | experiment | model_sha256 | N | phishing | legitimate | accuracy | precision | recall | F1 | specificity | false_negative_rate | false_positive_rate | ROC_AUC | PR_AUC | average_precision | TN | FP | FN | TP | threshold |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| LR | primary | df89f5e2b629b09f3e3f9fe2b6830726bd2d9eb17e5e51f3cdbf8f8a2dedb7bf | 29 | 28 | 1 | 0.9655172413793104 | 0.9655172413793104 | 1.0 | 0.9824561403508772 | 0.0 | 0.0 | 1.0 | 1.0 | 1.0 | 1.0 | 0 | 1 | 0 | 28 | 0.5 |
| RF | primary | 19be45a63832fa8670849a824db84ba37b9fe7b405ae9a7df7776d5aa8147bb7 | 29 | 28 | 1 | 0.9655172413793104 | 0.9655172413793104 | 1.0 | 0.9824561403508772 | 0.0 | 0.0 | 1.0 | 1.0 | 1.0 | 1.0 | 0 | 1 | 0 | 28 | 0.5 |
| ModernBERT | primary | 7ea2311d32ef766a51e3ccc25046f81c8bcdf80d6e3c07b3e42140822af25d43 | 29 | 28 | 1 | 0.9655172413793104 | 0.9655172413793104 | 1.0 | 0.9824561403508772 | 0.0 | 0.0 | 1.0 | 1.0 | 1.0 | 1.0 | 0 | 1 | 0 | 28 | 0.5 |
