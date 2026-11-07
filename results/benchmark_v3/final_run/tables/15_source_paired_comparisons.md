# 15 source paired comparisons

Exploratory machine-reviewed research; see exact denominators and limitations in FINAL_REPORT.md. CSV is authoritative; preview limited to30rows.

| model_A | model_B | paired_N | A_correct_B_wrong | A_wrong_B_correct | p_value | accuracy_difference | scope | holm_adjusted_p_secondary_family |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| LR | RF | 167 | 0 | 0 | 1.0 | 0.0 | secondary_exploratory_phishing_only_source_test | 1.0 |
| LR | ModernBERT | 167 | 20 | 0 | 1.9073486328125e-06 | 0.1197604790419161 | secondary_exploratory_phishing_only_source_test | 5.7220458984375e-06 |
| RF | ModernBERT | 167 | 20 | 0 | 1.9073486328125e-06 | 0.1197604790419161 | secondary_exploratory_phishing_only_source_test | 5.7220458984375e-06 |
