# Benchmark v2 confirmatory power decision

## Frozen statistical structure

- Unit: unique paired semantic scenario; C0–C3 variants do not add independent-sample credit.
- Primary endpoint: binary phishing prediction at the detector's frozen threshold.
- Family: H1, H2, and H3 independently for two frozen detectors, plus H4 detector interaction: seven primary tests.
- Family-wise alpha: 0.05.
- Multiplicity: exact Holm step-down across all seven p-values in every simulation replicate.
- Current simulation output: sensitivity analysis, not approved confirmatory assumptions.

## Sensitivity profile

For paired effect 0.04, discordant-pair rate 0.10, and the current deterministic simulation:

| Unique phishing scenarios | Minimum marginal Holm rejection power |
|---:|---:|
| 500 | 0.609 |
| 750 | 0.866 |
| 1,000 | 0.965 |

The conservative 0.02-effect profile remains below 0.80 even at N=1,000, while the optimistic 0.06 profile exceeds 0.80 by N=500. Power therefore depends materially on the effect and discordance assumptions.

## Recommendation requiring approval

Use **750 unique complete phishing scenarios** as the minimum recommended confirmatory target if the minimum meaningful paired effect is 0.04, discordance is 0.10, target marginal power is at least 0.80, and the current dependence sensitivity is accepted. Inflate the number constructed before review using a preregistered complete-set attrition estimate; do not replace rejected scenarios based on detector behavior.

Use a separate legitimate-control target driven by specificity confidence-interval precision. A provisional **500 legitimate scenarios** is reasonable for faculty review but is not frozen until the desired interval width and expected specificity are approved.

Before finalization, approve: effect assumptions separately for H1/H2/H3/H4, discordance rates, cross-test/detector dependence, target marginal versus joint power, complete-set attrition, target power, and legitimate-control precision. The final N must be fixed before generation and detector evaluation.
