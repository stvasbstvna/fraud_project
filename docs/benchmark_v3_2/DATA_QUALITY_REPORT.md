# Data quality report

| source_dataset | label | origin_type | N |
| --- | --- | --- | --- |
| gateway | phishing | uncertain_origin | 9 |
| mendeley | phishing | real_source | 2 |
| nus | legitimate | real_source | 1 |

Final source count 12; labels {'legitimate': 1, 'phishing': 11}; origins {'real_source': 3, 'uncertain_origin': 9}. Template representatives 12; all training/validation family overlaps excluded. No synthetic controls. English/SMS and financial function assessed in raw A/B/J source reviews. Source license evidence retained in SOURCE_EXPANSION_AUDIT.md. Duplicate and family edges preserved; old/new source count units are not interchangeable. Initial ambiguous NUS ID excluded. Sender authenticity remains unverified.

## Dataset limitations
Only one eligible legitimate source remains; its sender authenticity/origin is unresolved. Known real-source provenance is not proof of bank authorship. Rights-cleared does not establish label truth. Source imbalance, conservative family exclusions and finite candidate search limit population coverage.
## Model limitations
Reuse of small, imbalanced v3-trained models; probability outputs are uncalibrated. This experiment does not retrain or improve detectors. Frozen-artifact identity does not imply deployment quality.
## Generation limitations
Four conditions can overlap in actual surface changes; exact institution/numeric/placeholders constrain transformations. Rejected attempts and selective completeness produce survivorship effects. No outcome-driven rewrite optimization.
## Automated review limitations
Separate contexts are not statistically independent human annotation. Shared provider/model biases remain; generator and A share a snapshot. Confidence is subjective. Four initial source approvals required source-only policy exclusion, demonstrating fallibility.
## Statistical limitations
Below30legitimateframes, no adequately supported between-class or model-by-condition population comparison. Frame bootstrap cannot create support, and a degenerate interval on one control is not certainty. Conditions are repeated within frames; primary and available-pair cohorts differ.
## External validity limitations
Defanged public historical SMS are not representative current bank traffic. Prior pool inspection and review failures affect selection. No deployment FPR, temporal drift or universal model ranking.
## Causal inference limitations
Descriptive associations between surface distance and score movement do not establish linguistic causality. Semantic preservation is model-judged, not independently verified ground truth; no numeric semantic embedding similarity was measured.
