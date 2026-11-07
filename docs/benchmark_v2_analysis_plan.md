# Benchmark v2 statistical analysis plan

## Population and attrition

Primary paired analysis uses confirmatory-final-test scenarios with the complete approved condition set required by each contrast. Report condition-specific and lineage-stage attrition. Available-approved-pair analysis is sensitivity only. Pilot and quality-validation scenarios are excluded.

## Primary outcome and estimands

The confirmatory primary outcome is **binary phishing prediction at the detector's frozen threshold**.

- H1: paired recall difference `recall(C2) - recall(C0)`, separately per detector.
- H2: mean scenario-level difference `I(prediction_C0 != prediction_C2) - I(prediction_C0 != prediction_C1)`, separately per detector.
- H3: paired recall difference `recall(C3) - recall(C2)`, separately per detector.
- H4: one detector-by-transformation interaction test over the frozen primary formulation.

Transition tables describe discordant observations underlying H1/H3 paired effects. H2 uses a paired test or scenario bootstrap for its two boundary-change indicators. An ordinary signed score difference-in-change is algebraically C2 versus C1 because C0 cancels and is not a distinct estimand. Standardized within-model score changes are secondary.

## Confirmatory family

Exactly seven primary tests are frozen: H1, H2, and H3 independently for Logistic Regression and Random Forest (six), plus one H4 detector-interaction test. Holm correction controls familywise α=0.05 across all seven. Detector roles were not chosen using v2 performance. Power planning accounts for this family, complete-set attrition, and both detectors.

## Metrics and comparability

For each detector/condition report confusion matrices, recall/FNR, specificity/FPR, precision, F1, balanced accuracy, MCC, and intervals. Precision on the designed 50/50 benchmark does **not** estimate deployment precision under real phishing prevalence. Raw Logistic Regression and Random Forest probabilities are not assumed directly comparable: prefer within-model changes, standardized score changes, ranks, and boundary transitions unless independent calibration establishes comparability. AUROC, PR-AUC, Brier score, and calibration are secondary when appropriate.

## Secondary and exploratory analyses

Secondary endpoints include standardized score shifts, FNR, specificity/FPR, balanced accuracy, MCC, and justified calibrated metrics. Event, tactic, action, URL, length, source, naturalness, generator, and family subgroups are exploratory with separately declared Holm control. H5 remains exploratory unless a meaningful specificity threshold or margin is frozen before evaluation.

Cluster-bootstrap `scenario_id`, retaining all conditions, replicates, and crossed-generator variants together. Optional mixed-effects models include scenario random intercepts and do not replace paired primary analyses. Missing text is not imputed; report differential exclusion and sensitivity bounds. Null results are estimates with intervals, not proof of equivalence or confirmed degradation.
