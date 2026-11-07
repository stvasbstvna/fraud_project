# 15 source paired comparisons

Exploratory machine-reviewed research; see exact denominators and limitations in FINAL_REPORT.md. CSV is authoritative; preview limited to30rows.

| model_A | model_B | paired_N | A_correct_B_wrong | A_wrong_B_correct | p_value | accuracy_difference | scope | holm_adjusted_p_secondary_family |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| LR | RF | 194 | 0 | 0 | 1.0 | 0.0 | secondary_exploratory_phishing_only_source_test | 1.0 |
| LR | ModernBERT | 194 | 25 | 0 | 5.960464477539064e-08 | 0.1288659793814432 | secondary_exploratory_phishing_only_source_test | 1.788139343261719e-07 |
| RF | ModernBERT | 194 | 25 | 0 | 5.960464477539064e-08 | 0.1288659793814432 | secondary_exploratory_phishing_only_source_test | 1.788139343261719e-07 |
