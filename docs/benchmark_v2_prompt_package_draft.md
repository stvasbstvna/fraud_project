# Benchmark v2 safe prompt package — draft v0.1

**Status:** Draft for mentor/protocol review. It defines safe research transformations, not prompts for generating operational phishing. Every decision placeholder must be frozen before generation.

## 1. Condition lineage and what is actually known

The protocol already fixes the lineage `C0 → C1/C2` and `C2 → C3`, primary H1 as `recall(C2) − recall(C0)`, and primary H3 as `recall(C3) − recall(C2)`.

| Condition | Proposed operational role | Status |
|---|---|---|
| `C0` | Source-licensed or researcher-authored **non-LLM anchor**. No generator metadata. | Confirmed structural rule |
| `C1` | Minimal normalization limited to punctuation, capitalization, whitespace, and unambiguous typographical or grammar errors; no lexical substitution, clause reordering, fact/action/urgency change. | Confirmed closed transformation list |
| `C2` | Composite naturalization condition: natural short-message style while preserving the semantic frame. | Confirmed H1 comparison |
| `C3` | `C2` with a prespecified reduction in action explicitness; aggregate manipulation check required. | Confirmed H3 comparison |

The word **natural** is not a license to change meaning, make a message more persuasive, or remove a suspicious indicator because a detector uses it. It means better everyday SMS fluency under the frozen semantic frame.

## 2. Shared system instruction (all LLM conditions)

```text
You are producing a non-deployable cybersecurity research artifact.
Create exactly one short SMS-style text from the supplied structured semantic frame.

Preserve every required invariant exactly in meaning: label, claim, target action
category, scenario family, entity placeholders, amount/date placeholders, and URL
safety state. Do not add any fact, named organization, account, credential, payment
route, phone number, recipient information, live URL, real domain, or operational step.
All web references must remain defanged placeholders exactly as supplied.

Do not use or infer detector output, classification labels beyond the supplied research
label, model probabilities, or information about what text might evade a detector.
Return only JSON conforming to the supplied schema.
```

## 3. Required input object

```json
{
  "scenario_id": "B2-P-0001",
  "condition": "C2",
  "semantic_frame": {
    "population": "phishing | legitimate",
    "scenario_family": "<APPROVED_SCENARIO_FAMILY>",
    "claim": "abstract claim, not live operational content",
    "requested_action_category": "<APPROVED_ACTION_CATEGORY>",
    "tactic_tags": ["<APPROVED_TACTIC_TAG>"],
    "entity_placeholders": ["[BANK_NAME]"],
    "amount_date_placeholders": ["[AMOUNT]", "[DATE]"],
    "url_state": "none | defanged_placeholder",
    "prohibited_changes": ["..."],
    "length_bounds": {"min_chars": 0, "max_chars": 0}
  }
}
```

The actual JSON fields must match the project schema; this is a readable specification, not a replacement schema.

## 4. Condition instructions

### C0 — anchor

No LLM prompt. Record `creation_method: non_llm_anchor`; generator/provider/model metadata must be `null`, not `not_applicable`.

### C1 — minimal controlled rewrite (draft)

```text
Rewrite only mechanical or surface-level irregularities that the frozen C1 definition
explicitly permits. Preserve wording, sentence structure, action explicitness, and
all semantic invariants as far as possible. Do not improve persuasiveness, remove
urgency, add politeness, or substitute entities. If no permitted edit is possible,
return status "no_valid_variant" rather than copying the anchor.
```

The permissible operations are the closed list above. If none applies, return `no_valid_variant`; never broaden C1 after outcome inspection.

### C2 — composite naturalization

```text
Produce one concise, everyday SMS-style variant that expresses the supplied semantic
frame in fluent, natural language. Preserve the claim, action category, label,
entities/placeholders, dates/amount placeholders, defanged URL state, and all
prohibited changes. Do not introduce new operational detail or alter the action.
Keep within the supplied length bounds. Return JSON only.
```

### C3 — softened action-explicitness manipulation

```text
Starting from the supplied approved C2 text, create one variant with the same claim,
requested-action category, action channel, entities/placeholders, safety state, and
overall naturalness. Make only the wording of the existing action less direct or
abrupt. Do not remove the action, replace it with a different action, or add a new
action, consequence, urgency, amount, destination, credential, or operational
instruction. Return JSON only.
```

The protocol’s aggregate 1–5 action-explicitness review score is the manipulation check: C3 must be lower than paired C2 at the preregistered aggregate level. One reviewer tie must not automatically exclude an otherwise valid variant.

## 5. Required structured output

```json
{
  "scenario_id": "B2-P-0001",
  "condition": "C2",
  "text": "...",
  "invariants_check": {
    "claim_preserved": true,
    "requested_action_preserved": true,
    "label_preserved": true,
    "entities_placeholders_preserved": true,
    "no_operational_detail_added": true,
    "url_state_preserved": true
  },
  "generation_status": "candidate | no_valid_variant",
  "generator_metadata": {
    "provider": "<FROZEN_GENERATOR_PROVIDER>",
    "model": "<FROZEN_GENERATOR_MODEL>",
    "model_version": "<FROZEN_EXACT_MODEL_VERSION>",
    "prompt_id": "b2_c2_v0_1",
    "temperature": 0.2,
    "seed": null
  }
}
```

The self-check is only a machine claim. It cannot approve a record; the validator and human-review records decide inclusion.

## 6. Rejection rules

Reject before human review when any of the following occurs:

- output equals its source condition text;
- output contains a live URL/domain, active phone number, credential, account identifier, payment route, real person, or unapproved real organization;
- an invariant is missing or contradicted;
- the JSON does not validate;
- the condition-specific manipulation is absent or exceeds scope;
- duplicate text appears in another final-test scenario.

## 7. Versioning requirement

Never overwrite a prompt. Create a new prompt ID/version, record the exact change, and rerun the pilot calibration if it affects meaning, style, or condition separation.
