# Benchmark v2.1 current project status

## Status

`TECHNICAL_FREEZE_READY_EXTERNAL_ACTIONS_PENDING`

The v2.1 patch is integrated additively under isolated `benchmark_v2_1` paths. File, scale, condition, URL-safety, provenance, confirmatory-family, analysis-code, and power-output checks pass. Researcher-approved Option B replaces both the older H1–H4 family and the patch's twelve pairwise tests with a new seven-member dose-response family.

## Fixed technical design

- researcher-authored synthetic confirmatory anchors;
- 750 phishing frames and 500 legitimate controls;
- C0–C6 with 8,750 condition rows;
- 48-frame / 336-row pilot and 288 unrun C1–C6 generation jobs;
- OpenAI `gpt-5.4-mini-2026-03-17` candidate, temperature 0.2, top_p 1.0, one output/job, maximum two attempts;
- detector-independent linguistic-distance metrics;
- new seven-member dose-response Holm family;
- inactive generator and explicit generation lock;
- no detector feedback in generation or review.

## Not performed

- no v2.1 LLM API call or generated pilot output;
- no detector evaluation, retraining, threshold tuning, or detector-guided regeneration;
- no fabricated human review, agreement, adjudication, or manipulation result;
- no final dataset or confirmatory finding.

## External gates

Pilot generation requires a separate authorization after the preregistration artifacts pass checks. Then two independent detector-blinded reviewers must complete review, agreement/adjudication, and the aggregate manipulation gate. Full generation additionally requires attrition freeze and full readiness. Final detector evaluation remains blocked until full human review and final dataset hashing are complete.
