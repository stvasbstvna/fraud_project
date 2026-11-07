# Benchmark v2 preregistered hypotheses

These hypotheses precede v2 generation and evaluation. They are not findings. Conditions are paired within `scenario_id`; inference respects scenario clustering.

## H1 — Composite naturalization

- **Independent variable:** composite condition, `C0_template` versus `C2_natural`; fluency, lexical form, syntax, and conversational naturalness jointly change.
- **Primary outcome/estimand:** binary phishing prediction at the detector's frozen threshold; paired recall difference `recall(C2) - recall(C0)` separately for each detector.
- **Comparison:** paired phishing scenarios under C0 and C2.
- **Test:** paired binary test/exact McNemar with scenario-cluster interval for recall difference; transition tables describe discordant observations.
- **Support:** lower C2 recall/probability with an interval and transition imbalance consistent with meaningful deterioration.
- **Non-support:** negligible, uncertain, or opposite difference; balanced discordant transitions.
- **Limitations:** this is not a pure causal effect of naturalness. The bundled fluency, lexical, syntactic, and conversational changes cannot be separately attributed from this contrast.

## H2 — Surface dependence

- **Independent variable:** transformation magnitude (`C1_fluent` versus `C2_natural`, each relative to C0).
- **Primary outcome/estimand:** `I(prediction_C0 != prediction_C2) - I(prediction_C0 != prediction_C1)` per scenario and detector at frozen thresholds.
- **Comparison:** the two paired boundary-change indicators. An ordinary signed score difference-in-change is algebraically C2 versus C1 because C0 cancels and is not claimed as distinct.
- **Test:** paired test or scenario bootstrap for the two boundary-change indicators. Standardized within-model score changes are secondary.
- **Support:** materially larger confidence/boundary changes for C2 than C1.
- **Non-support:** similar, smaller, uncertain, or reversed C2 changes.
- **Limitations:** TF-IDF attribution is architectural, not proof that a specific token caused a decision.

## H3 — Action explicitness

- **Independent variable:** unchanged versus softened action wording, exclusively `C2_natural` versus `C3_natural_softened` for the primary test.
- **Primary outcome/estimand:** binary phishing prediction at the frozen threshold; paired recall difference `recall(C3) - recall(C2)` separately for each detector.
- **Comparison:** paired variants with identical requested-action category and channel.
- **Test:** exact McNemar and scenario-cluster bootstrap for C2→C3; the separate aggregate blinded 1–5 manipulation check uses median reviewer aggregation, retains ties as zero, and applies a minimum ordered-effect rule frozen before evaluation. A single reviewer tie never rejects a variant. Comparisons involving C1 are secondary.
- **Support:** C3 passes preservation review, has lower explicitness ratings than C2, and produces a meaningful paired boundary/confidence shift.
- **Non-support:** no reliable extra shift, or preservation review fails disproportionately.
- **Limitations:** C3 jointly contains naturalness and action-explicitness choices; it cannot be merged with C2 or interpreted as a pure naturalness effect.

## H4 — Detector differences

- **Independent variable:** detector (`TF-IDF + Logistic Regression`, `TF-IDF + Random Forest`) and condition.
- **Dependent variables:** paired transition categories and probability shifts.
- **Comparison:** detector-by-condition transition profiles on the same scenarios.
- **Test:** cluster bootstrap for between-detector contrast; optional mixed-effects logistic interaction model. Direction is not preregistered.
- **Support:** intervals show materially different transition/probability responses.
- **Non-support:** profiles and uncertainty are compatible with no detector difference.
- **Limitations:** only two frozen implementations and their fixed preprocessing/thresholds are represented.

## H5 — Legitimate banking controls (exploratory until margin freeze)

- **Independent variable:** condition/event features among legitimate controls.
- **Dependent variables:** specificity, FPR, balanced accuracy, MCC, calibration/Brier score.
- **Comparison:** legitimate versus phishing performance and legitimate subgroup/condition results.
- **Test:** binomial or cluster-bootstrap intervals; exact paired tests where legitimate conditions are paired. H5 becomes confirmatory only if a meaningful specificity threshold or comparison margin is frozen before evaluation.
- **Support:** phishing recall remains high while specificity is materially weak or poorly calibrated.
- **Non-support:** both recall and specificity are strong within uncertainty, or recall itself is weak.
- **Limitations:** legitimate-source representativeness and matching quality constrain population claims.
