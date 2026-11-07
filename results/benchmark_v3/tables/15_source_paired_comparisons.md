# 15 source paired comparisons

Exploratory machine-reviewed research; see exact denominators and limitations in FINAL_REPORT.md. CSV is authoritative; preview limited to30rows.

| model_A | model_B | paired_N | A_correct_B_wrong | A_wrong_B_correct | p_value | accuracy_difference | scope | holm_adjusted_p_secondary_family |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| LR | RF | 194 | 0 | 0 | 1.0 | 0.0 | secondary_exploratory_phishing_only_source_test | 1.0 |
| LR | ModernBERT | 194 | 33 | 0 | 2.3283064365386963e-10 | 0.1701030927835051 | secondary_exploratory_phishing_only_source_test | 6.984919309616089e-10 |
| RF | ModernBERT | 194 | 33 | 0 | 2.3283064365386963e-10 | 0.1701030927835051 | secondary_exploratory_phishing_only_source_test | 6.984919309616089e-10 |
