# Results changelog — incompatible versions are not pooled

| version | dataset_size | phishing | legitimate | models | conditions | complete_trajectories | threshold_crossings | main_result | major_limitation | what_changed_next |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| v1 | 143 verified historical phishing pairs; control denominator see original report | 143paired | not comparable here | LR/RF | paired original/rewrite | not the v3.2 definition | see preserved v1 evidence | Historical recall drop about0.6993percentagepoints; not rerun | Different protocol/population | Prospective multi-condition design |
| v2.1 automated pilot | 4sources/20available rows | 2 | 2 | LR/RF | C0-C6; C2missing | 0 | 0 | Primary completeness failed; exploratory only | Synthetic legitimate controls and source-label confounding | Real-source v3 acquisition |
| v3 final_run | 195 | 186 | 9 | LR/RF/ModernBERT actually fine-tuned | C0/C1/C4/C5/C6 | 7phishing/0legitimate | 0on39approvedpairs | 39pairs, conditioncounts8/11/10/10; exploratory | One negative test control, retrospective corrections | Newv3.2 prompts/source-review/generation; no pooling |
| v3.2 | 12 | 11 | 1 | same frozen v3 primary models | C0/C1/C4/C5/C6 | {"legitimate": 0, "phishing": 0} | {"LR": 0, "ModernBERT": 0, "RF": 0} | See new SUMMARY and paired tables only | Legitimate control target unmet; automated labels | Independent real controls and fresh research cohort |

Historical references: docs/benchmark_v3/FINAL_REPORT.md and docs/benchmark_v2_1/AUTOMATED_PILOT_FINAL_REPORT.md; v1 numbers are prior observations reported there, not new inference.
