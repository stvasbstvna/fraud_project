# HORIZONS Q&A

## Did the rewrites defeat the detectors?
Not as a general conclusion. Each detector had one additional phishing miss among 143 evaluated phishing pairs, but exact McNemar p=1.0.

## Why discuss confidence if recall barely changed?
Confidence can reveal sensitivity before a threshold crossing, but here the average change is slightly in the opposite direction and both 95% bootstrap intervals include zero. It is exploratory, not proof of failure.

## Are the 153 rewrites human-approved research data?
Yes. All 153 completed rewrites have recorded human approval. This does not make the paired effect statistically significant or remove the small legitimate-control limitation.

## Why are legitimate results weak?
There are only ten legitimate controls. The low specificity is concerning as a false-positive/generalization signal, but the estimate is unstable and distinct from rewrite robustness.

## Was the generator optimized against detector feedback?
No. Detector access and feedback were excluded from generation, and the models remained frozen.

## Is Benchmark v2 already a final benchmark?
No. The current pilot is researcher-authored, non-operational, and `final_benchmark_eligible=false`. It calibrates workflow and review logic only.

## What would justify a stronger claim?
Completed blinded human review, authorized final anchors, frozen prompts and generator assignments, adequate power for the preregistered testing family, and confirmatory paired tests at frozen thresholds.
