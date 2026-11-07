# Benchmark v2 review and naturalness rubric

Reviewers see scenario content but not detector outputs; condition labels are hidden where practical. Automated/LLM-assisted audit is never labeled human review and receives the same detector blinding.

## Human semantic decision

For each variant mark **approve**, **reject**, or **uncertain** after separately judging: semantic intent, requested action, action channel, label, entities/facts, absence of operational detail, distinction from other conditions, and condition fit. Rate naturalness and action explicitness independently from 1–5. Rejection requires a reason; uncertainty requires a note. A stratified 10–20% receives an independent second review. Report raw agreement and Cohen's kappa where applicable, then adjudicate disagreements without detector results.

## Condition-specific validation

- **C0:** template fidelity and preservation; it is not excluded merely for low naturalness.
- **C1:** correction fidelity, preservation, and minimal lexical/structural change.
- **C2:** naturalness, preservation, and composite-naturalization condition fit.
- **C3:** naturalness, preservation, condition fit, and reduced action explicitness versus paired C2.

Action explicitness uses 1 = highly indirect/softened and 5 = highly direct/abrupt. Variant-level reviewers judge C3 condition fit, but one reviewer's C2=C3 rating never automatically rejects a variant. Ratings are aggregated by the median across blinded reviewers within variant, then paired C2−C3 within scenario. Ties are retained as zero differences. Before evaluation, freeze a minimum acceptable aggregate ordered effect (for example a positive median paired difference plus a confidence bound or signed-rank criterion); it remains `TBD_BEFORE_EVALUATION`. If aggregate direction/effect fails, pause the C3 confirmatory contrast and adjudicate condition fit using blinded rationales—do not select variants by detector results.

Use ordinary Cohen's kappa for categorical decisions. Use weighted kappa or an intraclass correlation coefficient, with the exact form frozen in advance, for 1–5 naturalness and explicitness ratings. Adjudication records the original ratings, tie status, adjudicator, rationale, and timestamp.

## Five-point naturalness scale

Naturalness is not persuasiveness, harmful effectiveness, or detector evasion.

1. **Clearly unnatural:** fragmented/corrupted, strong template artifacts, sender inconsistency, or email-like formatting that is implausible for SMS.
2. **Mostly unnatural:** understandable but stiff, repetitive, poorly coherent, or implausibly formatted/long for contemporary SMS.
3. **Mixed/plausible with issues:** generally coherent SMS but contains noticeable templating, awkward phrasing, excess length, or a minor sender-role mismatch.
4. **Natural:** concise enough, grammatically/conversationally coherent, sender-consistent, and plausibly contemporary with no important template artifact.
5. **Highly natural:** exceptionally fluent and economical SMS realization while preserving the frame; not rated higher merely because it seems persuasive or clickable.

Reviewers consider SMS plausibility, concision, grammar/conversation, template artifacts, sender-role consistency, and unnecessary email formatting. They must not use whether they personally would click.

## Preregistered exclusion reasons

- `schema_failure`
- `semantic_intent_changed`
- `requested_action_changed`
- `label_changed`
- `entity_or_fact_changed`
- `operational_detail_added`
- `live_or_unsafe_destination`
- `condition_violation`
- `exact_or_near_duplicate`
- `corrupted_or_unreadable_text`
- `naturalness_below_threshold`
- `licensing_or_provenance_failure`
- `other` (free-text explanation required)

No global naturalness threshold is implied. The remaining aggregate C2-versus-C3 effect threshold and ordinal agreement statistic require preregistered approval before evaluation. Exclusions occur before detector evaluation wherever possible and never because a detector was correct or incorrect.
