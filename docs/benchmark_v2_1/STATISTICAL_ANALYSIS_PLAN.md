# Prospective statistical analysis plan — canonical-frozen-space-v1

Written 2026-11-06 before any new v2.1 detector scoring. No v2.1 outcome, p-value or confidence interval is available. This plan explicitly revises the distance representation used in the archived flat v2.1 plan. It does not amend old results or claim new power from old simulations.

## Primary question and family

Does frozen detector response vary systematically with reviewed linguistic transformation? English phishing-labelled source frames with complete approved C0–C6 sets and both model outputs form the primary population. Do not model numeric condition labels as equal-spaced doses: C2/C3 are directness manipulations. Use measured surface distance and prespecified categorical contrasts.

For each frame and detector regress clipped logit probability `log(p/(1−p))`, p clipped only after validation to [1e−6,1−1e−6], on measured distance across seven conditions. Average the two detector slopes **within frame**, then test the mean across frames. Repeat for the false-negative indicator. Undefined zero-distance slopes cause explicit design failure, not silent row exclusion. The average-detector estimand is not either detector individually.

One two-sided Holm family at FWER 0.05 contains exactly seven tests:

1. H1_DISTANCE_LOGIT: mean frame detector-average logit-distance slope = 0.
2. H2_DISTANCE_FN: mean frame detector-average miss-distance slope = 0.
3. H5_C0_C1: detector-average logit(C1)−logit(C0) = 0.
4. H6_C2_C3: detector-average logit(C3)−logit(C2) = 0.
5. H7_C0_C4: detector-average logit(C4)−logit(C0) = 0.
6. H8_C0_C5: detector-average logit(C5)−logit(C0) = 0.
7. H9_C0_C6: detector-average logit(C6)−logit(C0) = 0.

One-sample two-sided t tests operate on one effect per independent frame, not one row per variant. Report mean effects, 95% percentile frame-bootstrap intervals (seed 42, 10,000 draws), raw and Holm adjusted p-values. Resampling effects retains all paired conditions/model information used in each effect. Effects based on fewer than two frames have no p-value; all-zero effects yield p=1; constant nonzero effects have undefined t inference, reported as such. Undefined tests remain in the multiplicity family (p=1 only for the adjustment algorithm), never become significance claims. Bootstrap intervals are descriptive marginal intervals, not simultaneous familywise intervals.

## Assumptions and limitations before confirmatory release

Independent frame effects, appropriate sampling population and adequate frame-level approximation are prerequisites. Near-duplicate/template families can violate independence even after exact deduplication. At present 22,406 within-entity near-duplicate pairs remain and candidate labels are unvalidated: **confirmatory analysis is not currently justified**. Before real data release, define template/campaign clusters and either select independent frames prospectively or amend to cluster-aware resampling/modeling before outcomes. Do not represent this skeleton as a completed preregistration or guaranteed adequate power. Binary slope tests can be sparse; assess pilot outcome-independent construction and simulation assumptions, not whichever test later achieves significance. The old synthetic power simulations do not establish power for the revised source distribution/metric.

## Supporting and exploratory outputs

Per-model/condition recall, FNR, precision, F1, accuracy, score shifts, transitions, confusion matrices, medians and distance components are descriptive. Legitimate controls/FPR are a separate population, not mixed into phishing endpoints. Plot paired frame-bootstrap confidence intervals for score differences, and examine detector-specific associations/heterogeneity as exploratory; do not label these additional comparisons confirmatory. No causal claim that shared vocabulary caused an error follows from a high score or distance correlation.

## Missingness and selection

No imputation. Confirmatory matrix requires exactly one C0–C6 observation per selected frame for both frozen models, valid finite probabilities, invariant metadata and two content-bound approvals. Exclusions and replacement/attrition rules must be frozen without detector information after pilot semantic review. Report all candidates, all failed generations/reviews and complete-case losses by source/label/condition. Available-pair analysis is sensitivity only. No significance-driven test switching or example-based statistical selection.
