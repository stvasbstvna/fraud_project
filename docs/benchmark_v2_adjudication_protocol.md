# Benchmark v2 blinded adjudication protocol

Adjudication occurs before detector evaluation and never includes predictions, probabilities, thresholds, model errors, or detector-selected examples.

## Review and aggregation

Each candidate is reviewed independently by two reviewers. Required categorical judgments are semantic intent, requested action, action channel, label, entity/fact preservation, operational safety, condition fit, naturalness/grammaticality, banking plausibility, and condition distinguishability. Action explicitness is rated from 1 (indirect/softened) to 5 (direct/abrupt).

- Any `no` on semantic intent, requested action, channel, label, entity/fact preservation, or safety sends the candidate to adjudication and presumptive exclusion.
- `uncertain`, missing review, or reviewer disagreement requires adjudication; it is never approval.
- C3 must preserve the C2 action while expressing it less directly. Removing or replacing the action is a preservation failure.
- One reviewer’s tied C2/C3 explicitness rating does not automatically reject a variant. Ties contribute zero to the preregistered aggregate manipulation check.
- Safety failures and live/operational destinations are excluded objectively and are not repair-selected using detector results.

## Adjudication outcomes

The blinded adjudicator records `approved`, `rejected`, or `needs_reconstruction`, cites the failed criterion, links both source review IDs, and timestamps the decision. Reconstruction is permitted only for prespecified semantic, format, or safety failures before freeze; it creates a new variant version and requires fresh review. No reconstruction is allowed because of detector behavior.

If the aggregate C3 manipulation check fails, pause H3 and revise the condition only in the quality-validation population. The confirmatory population remains untouched. After prompt revision, increment prompt/package versions and rerun blinded quality review.

Incomplete reviews are excluded from the primary complete-approved-set population. They may enter only a clearly labeled sensitivity analysis after the protocol-defined handling rule is applied.
