# Benchmark v2 pilot review instructions

This review calibrates the schema, rubric, and C0–C3 condition logic. It is not detector evaluation, and it cannot support a claim that a detector is weaker.

The sample contains six complete scenarios: three phishing-labelled and three legitimate-labelled, with all four conditions for each scenario. Selection is deterministic (`seed=20260827`), maximizes scenario-family and style-slot diversity within each population, and does not use detector outputs.

## How to review

Review all four variants belonging to one `scenario_id` together. Record a separate decision for each variant. Do not edit identifiers, labels, condition names, claims, requested-action categories, text, or warnings.

For each row, complete:

- `semantic_intent_preserved`: the generic claim and communicative purpose are unchanged.
- `requested_action_preserved`: the action category is unchanged; C3 may only soften how directly review/open is requested.
- `label_preserved`: the intended phishing or legitimate class remains unchanged.
- `entities_placeholders_preserved`: generic entities and placeholders are retained; nothing real is substituted.
- `no_operational_detail_added`: no live URL, phone number, credential, payment route, account detail, person, or real brand is introduced.
- `rewrite_is_different`: C1–C3 differ from their parent wording; for C0, judge whether it is a usable anchor.
- `condition_fit`: C0 is an anchor; C1 is minimal normalization; C2 is natural direct wording; C3 preserves C2 meaning while making only the review/open request less explicit.
- `action_explicitness_1_to_5`: 1 means implicit; 5 means very explicit.
- `reviewer_id`: a stable non-personal reviewer code.

Categorical criteria use `yes`, `no`, or `uncertain`.

## Decision rule

- `approved`: every categorical criterion is `yes` and the explicitness rating is present.
- `rejected`: at least one categorical criterion is `no`; enter the exact reason in `rejection_reason`.
- `needs_adjudication`: no criterion is `no`, but at least one is `uncertain`, or condition fit remains ambiguous.
- `pending`: the review is incomplete.

Blank or pending fields are never approvals. Disagreement between reviewers requires adjudication. The pilot remains `final_benchmark_eligible=false` regardless of review outcome.
