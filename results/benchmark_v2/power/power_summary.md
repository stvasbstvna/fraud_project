# Benchmark v2 Holm-family power sensitivity analysis

**Not a final sample-size freeze.** The seven-test Holm procedure is implemented exactly, but the profiles are sensitivity values rather than approved confirmatory assumptions.

| Profile | N | Effect | Discordance | Minimum test power |
|---|---:|---:|---:|---:|
| conservative | 500 | 0.020 | 0.100 | 0.057 |
| conservative | 750 | 0.020 | 0.100 | 0.137 |
| conservative | 1000 | 0.020 | 0.100 | 0.229 |
| target_sensitivity | 500 | 0.040 | 0.100 | 0.609 |
| target_sensitivity | 750 | 0.040 | 0.100 | 0.866 |
| target_sensitivity | 1000 | 0.040 | 0.100 | 0.965 |
| optimistic | 500 | 0.060 | 0.120 | 0.960 |
| optimistic | 750 | 0.060 | 0.120 | 0.996 |
| optimistic | 1000 | 0.060 | 0.120 | 1.000 |

Exact conditional-binomial McNemar p-values are calculated for each simulated paired comparison and Holm step-down correction is applied jointly across all seven p-values in every replicate.
