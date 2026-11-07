# Benchmark v3.2 implementation plan

User specification: attachment 694aaa1f-ea1b-430f-899f-8d8b3db9cdde/Pasted text.txt, all 61 sections. Explicit instruction to execute every possible stage supplies authorization to proceed without a design approval pause.

Architecture: additive Python pipeline, immutable content-addressed calls, fixed external prompt files, existing final v3 primary model references. Independent work domains: source expansion audit, paired analysis, figure exports. No old namespace mutations, no model tuning or detector feedback to reviewers.

Alternatives: retraining on expanded controls would change the underlying detector and add fitting uncertainty; reusing models provides a stable robustness comparison. Choose reuse if new sources can be screened free of primary training/validation exact or template overlap. Existing training controls are prohibited in the robustness cohort. Source scarcity is reported rather than fabricated.

- [ ] Snapshot all protected paths and save specification; freeze model references.
- [ ] Implement tested immutable IO, source/rewrite evidence binding, deterministic safety/retry/complete-case rules.
- [ ] Expand legitimate candidate search locally and through primary-source rights evidence. Audit family overlaps against final v3 fitting/validation rows and deduplicate sources.
- [ ] Freeze all source, generation and rewrite review prompts with registry hashes, role snapshots, retry policy and statistical plan before any new scoring.
- [ ] Run real source A/B semantic review and disagreement adjudication, retain failures. Select up to 100 per class using fixed source-only hash order.
- [ ] Run C1/C4/C5/C6 generation with at most one quality retry, then every generated attempt receives deterministic and separate semantic A/B review with adjudication for disagreements.
- [ ] Freeze source/matrix/complete flags, compute distances using frozen LR vectorizer; score C0 and approved rewrites with existing frozen models only.
- [ ] Produce separate complete-case and available-pair statistics, class-separated transitions, ten main figures plus two manipulation figures, exact plotting data and metadata.
- [ ] Produce required evidence index, ledgers, catalogs, 27-section report, presentation notes and historical changelogs without pooling versions.
- [ ] Run full tests and independent final review; verify all protected hashes and raw evidence; record unmet targets honestly.

Analysis is exploratory regardless of size because source selection, automated labels, related prior pool inspection and unknown upstream dependencies prevent an independent confirmatory claim. Complete-case minima and manipulation outcomes will be reported, not forced.
