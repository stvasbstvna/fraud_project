# v2.1 failure analysis and v2.2 prevention

Evidence inspected before implementation: `docs/benchmark_v2_1/AUTOMATED_PILOT_FINAL_REPORT.md`, `results/benchmark_v2_1/AUTOMATED_PRESENTATION_SUMMARY.md`, `automated_pilot/source_summary.json`, `condition_attrition.csv`, `frame_attrition.csv`, source/rewrite/adjudication CSVs, `available_pair_manipulation_check.json`, actual available-pair predictions, generation prompts C1–C6 and source-review prompt, original-source audit, source selection code, and Figure2 probability-change plot. Historical evidence remains unchanged.

The v2.1 run made 135 research calls and generated 24 variants. It yielded 16 approved variants from four sources but zero complete seven-condition cases. Both detectors flagged all 20 available rows. Those score observations do not validate the failed design.

| Failure | Concrete v2.2 prevention | Implementation/evidence boundary |
|---|---|---|
| 1. Four final source frames | Minimum 16 per class before generation; no tiny available-pair fallback | Enforced source-capacity stop and source gate |
| 2. Two controls | Compute optimistic distinct-family control capacity first | Implemented; counts are candidates, never approvals |
| 3. All controls synthetic | <=25% synthetic controls; independently supported real SMS prioritized | Implemented gate; unknown authorship cannot be called real |
| 4. Labels confounded with source | Multiple groups per class, class-specific 50% cap, shared-label source required | Implemented; target three groups remains prospective |
| 5. C2 zero approvals | Determine eligibility before generation; already-direct/no-action excluded from C2 | Deterministic triage implemented; semantic eligibility remains NOT RUN |
| 6. C1 copies | >=2 lexical substitutions plus semantic meaningfulness; punctuation-only fails | Surface check implemented; prospective prompt v22.1, not prevalidated |
| 7. No complete C0–C6 trajectory | Primary core C0/C1/C4/C5/C6, separate secondary C2/C3 | Core-completeness function tested; no accepted benchmark yet |
| 8. Broad event phrase treated as entity | Institution-only literal span; event, amount, time, product and destination stored separately | Typed candidate schema and institution precision screen tested; fresh semantic annotations not fabricated |
| 9. Dates masked as phones | Date/time/amount spans protected before phone rules; account/reference IDs separately typed | Regression tests, original inputs re-read rather than damaged old safe text |
| 10. Selective condition survival | Report eligibility/attrition; use only complete primary core, minimum 12+12 | Scoring precondition tested; no partial diagnostic scoring fallback |
| 11. No confirmatory analysis | Source freeze, 4+4 prompt prepilot, approval/manipulation gates, then benchmark freeze before scoring | Protocol fixed; dependent runtime stages remain unimplemented/unrun if source stop fails |
| 12. No representative trajectory | Choose median frame-average absolute movement among complete cases; deterministic ID tie-break | Prospective rule only; no example presented without complete cases |
| 13. Source imbalance | Class-specific source capacity and stratification before generation | Source gate tested; source audit reports held groups separately |
| 14. Uncertain labels | Ham is not banking legitimacy; spam not phishing; scam requires banking/phishing adjudication; A/B >=0.80 | Label mapping and pending fields implemented; fresh machine review only if source capacity can meet minimum |

Additional defect: v2.1's source rule required a nonempty requested action even for legitimate informational alerts. v2.2 allows `requested_action=NONE` with an explicit message function. This makes C2/C3 ineligible, not the legitimate source invalid. A bank notification is not automatically malicious just because it mentions a link, nor legitimate merely because a source calls it ham.

Typed defanging preserves ordinary dates, times and amounts as literal facts while recording their span types. It redacts operational endpoints and sensitive IDs. This is a safety/structure improvement, not semantic validation. Institution and event fields still require fresh multi-pass review.

No correction is claimed empirically successful until the required source and prompt gates pass. Tests establish software behavior; they cannot replace real control provenance or demonstrate successful linguistic manipulation.
