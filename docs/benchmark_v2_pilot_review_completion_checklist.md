# Benchmark v2 pilot human-review completion checklist

Reviewers remain blinded to detector identities, predictions, probabilities, thresholds, features, and errors.

For every sampled scenario, review C0–C3 together and complete every categorical and ordinal field:

- [ ] semantic intent is preserved;
- [ ] requested action category is preserved;
- [ ] C3 is less explicit than paired C2;
- [ ] C3 softens but does not remove the action;
- [ ] entities/placeholders are preserved;
- [ ] channel is preserved;
- [ ] URL/safety state is preserved and no operational detail is introduced;
- [ ] wording is natural and grammatical;
- [ ] there is no accidental semantic drift;
- [ ] `reviewer_id`, decision, reason where applicable, and notes are complete;
- [ ] no detector-derived field or result is visible.

Two reviewers must finish the required sample. Disagreements, uncertain judgments, C3 failures, semantic failures, and missing reviews go to detector-blinded adjudication. Pilot approval never makes a pilot row eligible for final evaluation.

## Required formula-driven summary sheet

When the spreadsheet editing runtime is available, add a `Review Summary` sheet without changing review cells. It must calculate from the review worksheet:

- reviewed: nonblank decision count;
- approved/rejected/needs-adjudication: `COUNTIF` by decision;
- unresolved: total rows minus reviewed;
- disagreement count: paired reviewer decisions differ for the same `variant_id`;
- C3 failures: C3 rows where condition fit or requested-action preservation is `no`, or the paired explicitness ordering fails;
- semantic-preservation failures: `semantic_intent_preserved="no"`.

No count may be hardcoded and blank decisions must remain blank. The current workbook has no fabricated judgments; summary-sheet authoring is pending because the required spreadsheet artifact runtime was unavailable in this session.
