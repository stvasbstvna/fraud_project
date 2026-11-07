# Available-pair diagnostic analysis — declared before detector scoring

Primary automated C0–C6 pilot outcome: **zero complete cases**. Twenty-four generated outputs yielded sixteen approved variants; seven exact C0 copies and one failed literal-entity check excluded eight. No semantic regeneration is allowed. Keep this outcome and all failed outputs intact. No detector probabilities have yet been computed for this branch.

The existing statistical plan permits available pairs as sensitivity only. This document specifies a separate, explicitly **exploratory incomplete-case** diagnostic freeze before any detector scoring. It neither waives the primary completeness rule nor declares a validated 48-frame pilot. It uses the four machine-approved source baselines plus all sixteen approved generated variants, excluding all eight rejected outputs. It retains machine-review provenance and every relevant prompt/config/model/data hash. Primary frozen CSV remains empty with an explicit NOT FROZEN manifest.

## Population and missingness

The available-pair dataset has twenty rows from four sources: two phishing-labelled Mendeley examples and two synthetic legitimate controls. Label and source are confounded. Counts vary by condition: C0=4, C1=1, C2=0, C3=4, C4=4, C5=4, C6=3. Report class-specific frame counts and paired-baseline denominators for every statistic. C1 has no approved phishing variant; C2 has no approved variant. Missing recall/FNR/FPR/means stay missing, never zero. Do not rank all seven conditions as if the populations were identical.

C0/C3/C4/C5 share the same four frames and may be compared descriptively as a common available subset. C6 has a different subset; C1 is a single legitimate example. No full seven-condition inference can be performed. Missingness depends on generation/validation, so available-pair effects are selection-dependent and not unbiased estimates for all requested rewrites.

## Outcomes and analysis

Use unchanged historical model binaries, fitted vectorizers and fixed threshold 0.5. Read only the immutable available-pair freeze for scoring. Preserve original pipeline predict tie behavior. Compute per-condition/class counts, confusion metrics, C0-relative signed/absolute movements, medians, frame-bootstrap intervals (seed 42, 10,000 draws), and both error/recovery directions for phishing and legitimate controls. Bootstrap intervals with one/two source frames are descriptive and cannot establish population precision.

The seven-member Holm family from the primary plan is **NOT RUN** because no complete case exists. No new hypothesis replaces it after viewing significance. For exploratory distance associations, summarize per-frame signed/absolute movement slopes against the frozen-space composite on that frame's available variants, retaining frame dependence; show frame counts, descriptive correlations and resampling intervals. No inferential p-value or significance claim is made for these incomplete, tiny samples. LR/RF movement correlation is descriptive, not evidence of TF-IDF causality.

## Tables, figures and examples

Tables report the incomplete-case validation/evaluation population explicitly. Counts must reconcile to the twenty-row freeze. Figures 1–4 may be produced with missing-condition gaps and visible N labels; Figure 3 uses separate LR/RF panels. A full C0–C6 representative trajectory and qualitative prompt-trajectory table are **not available**, because no eligible complete frame exists. Do not fill gaps with rejected outputs or choose a dramatic incomplete frame and call it the planned representative. Extreme cases may be ranked separately as descriptive available-pair examples.

Main conclusion must remain: automated review/generation ran, but the prespecified complete pilot failed its construction/completeness criteria. Diagnostic detector behavior can be described only for the saved approved available pairs. No robust ordering of C0–C6, general recall reduction, semantic ground truth, or lexical causality is established. Disclose that automated semantic review was used rather than independent human annotation.
