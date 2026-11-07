# Benchmark v2 power-analysis plan

No final count is frozen. Power is based exclusively on unique untouched confirmatory-final-test scenarios. Prompt-development pilots are outside Benchmark v2; quality-validation scenarios are excluded from confirmatory inference. Neither population, nor conditions, replicates, or fully crossed generator variants, adds independent confirmatory sample size.

## Inputs to freeze

Estimate assumptions from independent literature or excluded pilot/quality populations: baseline recall/specificity, minimum meaningful paired difference, discordance, probability-shift variance, exclusion/complete-set attrition, subgroup prevalence, alpha, power, and Holm adjustment. Determine separate final-test phishing and legitimate counts. Record separate provisional pilot, quality-validation, and final-test counts rather than dividing one total.

The confirmatory family contains seven tests: H1, H2, and H3 for each frozen detector plus one H4 detector-interaction test. Final simulation must apply Holm across these seven correlated tests and demonstrate power under complete-set attrition. The utility's unadjusted McNemar approximation is only a sensitivity input, not the final justification.

## Binary paired changes and recall

For phishing scenarios, size exact McNemar comparisons from expected discordant proportions `p10` and `p01`; their difference is the targeted recall change and their sum is the discordant rate. Compute across plausible ranges and verify the normal approximation with exact/binomial simulation near the chosen design. Inflate for preregistered exclusions and any replicate clustering. Recall intervals will also be checked for acceptable precision.

H2 requires simulation or bootstrap-based planning for the paired indicators `I(C0 != C2)` and `I(C0 != C1)`, including their within-scenario dependence. It is not powered as an ordinary score difference-in-change.

## Specificity

Repeat the paired procedure on legitimate scenarios using expected specificity/FPR and legitimate discordance. Phishing sample size cannot substitute for legitimate-control power. Precision requirements for specificity and rare false positives may dominate the legitimate target.

## Probability shifts and calibration

Use pilot-independent estimates of the standard deviation of within-scenario probability differences. Size paired/clustered tests or simulations for the smallest meaningful mean shift. Calibration and Brier analyses require enough outcomes across probability ranges; if sparse, report descriptive curves and intervals rather than overfit calibration tests.

## Clustered variants and subgroups

Resample and simulate at `scenario_id`. If multiple replicates are added, apply a design-effect or hierarchical simulation using plausible intraclass correlations; never multiply the scenario count by variants. Ensure each confirmatory subgroup has adequate scenarios after event/action/source stratification. Low-frequency subgroups remain explicitly exploratory and receive multiplicity correction.

## Reproducible utility

`src/benchmark_v2_power_analysis.py` treats `--phishing-count` and `--legitimate-count` as confirmatory-final-test counts. Optional pilot/quality counts are reported separately and never credited toward power. The approximation is not a universal required size; verify with exact clustered simulation before freeze.

```powershell
uv run python .\src\benchmark_v2_power_analysis.py `
  --baseline-recall 0.95 --expected-recall-difference 0.04 `
  --discordant-pair-rate 0.10 --alpha 0.05 --power 0.80 `
  --phishing-count 500 --legitimate-count 500 --variants-per-scenario 4
```

The baseline recall is contextual; the paired size is driven by the assumed difference and discordance. Assumptions must satisfy `discordant_pair_rate >= abs(expected_recall_difference)`.
