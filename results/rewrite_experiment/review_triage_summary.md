# Benchmark v1 rewrite review triage summary

> Offline deterministic triage only. This is not human review and cannot establish semantic preservation or naturalness.

- Eligible completed rewrites: **153**
- High risk: **14**
- Medium risk: **100**
- Low risk: **39**
- Human decisions prefilled: **0**

High risk means at least one new operational detail, missing defanged URL/placeholder, exact or normalized equality, or a duplicate rewrite. Medium risk means no high-risk flag but possible entity-token loss/addition, an extreme length ratio outside `0.55–1.8`, or token overlap below `0.45`. Low risk means no deterministic flag.

The queue contains no detector predictions or probabilities. Reviewers must independently assess semantic intent, requested action, label preservation, and naturalness. Triage never approves or rejects a row.
