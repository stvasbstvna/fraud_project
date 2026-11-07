# Benchmark v2 generation, review, and freeze runbook

## Phase 0 — decisions before any generation

1. Fill every `TBD` in the freeze register.
2. Confirm source authorization for every C0 anchor.
3. Freeze scenario-family and class distributions.
4. Freeze the generator pool, stratified scenario-level assignment, prompts, schema, settings, and rejection rules.
5. Keep detector outputs inaccessible to whoever generates/reviews variants.

**Stop condition:** if a decision changes after seeing detector results, classify later analysis as exploratory rather than confirmatory.

## Phase 1 — detector-blinded pilot

Purpose: assess generation feasibility and calibrate review—not estimate the final detector effect.

- Sample a small, stratified set across phishing/legitimate populations and scenario families.
- Generate candidates under the frozen draft package.
- Run schema/safety/duplicate checks.
- Two human reviewers independently rate candidates using the v2 rubric.
- Estimate: candidate rejection rate, complete-condition-set attrition, review time, inter-rater agreement, and distribution of manipulation-check scores.
- Do not run or inspect detector outcomes to choose a model, a prompt, or examples.

## Phase 2 — revise once, then freeze

Permitted pilot revisions: clarify an ambiguous invariant, fix a validator bug, or replace an unavailable generator. Record the version change and rationale.

Not permitted: modifying prompts to cause more false negatives, choosing a model because it lowers recall, or changing thresholds after looking at final-test detector outcomes.

Freeze the final source manifest, prompts, generator assignment, thresholds, reviewer instructions, and statistical plan.

## Phase 3 — final generation and automatic triage

For each assigned scenario:

1. Produce candidates only for the preassigned condition/generator block.
2. Validate JSON Schema.
3. Apply automated checks: defanged URLs, placeholder symmetry, no prohibited entities/details, length bounds, duplicate IDs/text, lineage, generator metadata.
4. Save each candidate and its rejection reason. Never silently replace it.
5. Present remaining candidates to reviewers without detector predictions.

## Phase 4 — human review

Each reviewer assesses:

- semantic intent preserved;
- requested action preserved;
- label preserved;
- entities/placeholders preserved;
- no operational detail added;
- rewrite differs;
- condition fit;
- 1–5 action explicitness rating where applicable;
- optional notes and rejection reason.

### Decision rule

- **Approve:** all binary invariants pass and condition fit passes.
- **Reject:** any safety or semantic invariant fails.
- **Adjudicate:** reviewer disagreement or low-confidence rating.

Compute Cohen’s kappa for categorical decisions; weighted kappa or ICC for the 1–5 rating, as frozen in the protocol. Human reviewers should not know which detector will be evaluated or the model’s output.

## Phase 5 — complete-set freeze and analysis

1. Include a scenario in the primary analysis only if its required condition set is fully approved.
2. Hash and freeze the approved final-test files.
3. Run each frozen detector exactly as archived, at its frozen threshold, once per condition.
4. Conduct only the prespecified primary contrasts and Holm correction.
5. Report incomplete/available-pair results as sensitivity analysis only.

## Minimum audit trail per record

`scenario_id`, source manifest ID, frame ID/version, condition, parent condition ID, creation method, generator/provider/model/version, prompt ID/version, parameters, generation timestamp, validator result, review decisions, adjudication decision, final inclusion status, and hash.

