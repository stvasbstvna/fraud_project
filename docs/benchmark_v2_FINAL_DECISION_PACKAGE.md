# Benchmark v2 final human research-design approval package

**Current gate:** `TECHNICAL_FREEZE_READY_HUMAN_DECISIONS_PENDING`  
**Generation:** prohibited. **Detector evaluation:** prohibited.

This document collapses 19 active markers into **seven independent approval decisions**. Checking a box records a choice but does not itself change configuration; implementation and readiness verification follow sign-off.

## Decision 1 — source strategy and benchmark composition

| Option | Provenance and authorization | Control / reproducibility | Ecological validity | Contamination risk | Confirmatory suitability |
|---|---|---|---|---|---|
| A. Authorized real-world anchors | SmishX/SmishTank only where dataset-content reuse, transformation, privacy, attribution, and redistribution rights are evidenced row by row. SmishTank redistribution is currently unconfirmed. | Lower control over strata and wording; reproducible only with immutable accessible source/version/hash. | Highest potential realism, subject to source representativeness. | Highest: overlap with detector training/public corpora must be checked and clustered. | Suitable only after authorization and contamination audit. |
| B. Researcher-authored synthetic anchors | Internal authoring declaration, provenance log, privacy review, and public-use authorization are required. | Highest control and easiest deterministic redistribution. | Lower: may not reproduce real user/institution language or error distribution. | Lower but not zero; authoring may be influenced by known examples. | Suitable for controlled causal contrasts, with explicit external-validity limitations. |
| C. Hybrid | Separately authorized real anchors plus researcher-authored controls, with source type frozen and stratified. | Strong control plus reproducible source-specific reporting; more complex design. | Better balance between realism and control. | Must audit real subset and prevent source/condition confounding. | Neutral recommendation if enough real anchors are legally usable; source-stratified sensitivity analysis required. |

**Neutral recommendation:** approve Option C only if sufficient real anchors obtain explicit authorization and contamination checks before freeze; otherwise use Option B and narrow claims to controlled synthetic robustness. Synthetic-only is not scientifically superior—it trades ecological validity for control and redistribution clarity.

- [ ] Option A approved
- [ ] Option B approved
- [ ] Option C approved
- [ ] Source proportions/distributions approved: ____________________
- [ ] Authorization evidence and public-example permissions reviewed

## Decision 2 — generator instrument and assignment

Inactive candidate:

| Field | Candidate | Rationale |
|---|---|---|
| Provider/model/version | OpenAI / `gpt-5.4-mini` / `gpt-5.4-mini-2026-03-17` | Exact snapshot already recorded in repository tooling; selection is not based on detector results. |
| Temperature | 0.2 | Limited variation while allowing a rewrite; lower variance than creative sampling. |
| `top_p` | 1.0 | Avoids simultaneous tuning of two sampling controls. |
| Seed | none; deterministic sampling not claimed | Provider seed behavior is not assumed. Determinism comes from frozen inputs/logging, not an unsupported claim. |
| Generations/job | 1 | Prevents outcome-free candidate selection from becoming undocumented researcher choice. |
| Maximum attempts | 2 | Bounds technical/schema/safety retries and cost. |
| Max output tokens | 500 | Sufficient for one short structured SMS record without encouraging extra content. |
| Detector context | strictly prohibited | Prevents detector-guided optimization and leakage. |

Retries are permitted only for transport, rate-limit, malformed JSON, schema, or objective safety failure. URLs remain defanged; intent/action/entities/channel/safety state remain invariant; C3 softens the same action and generation is not adversarial optimization.

- [ ] Approve
- [ ] Modify: ______________________________________________________
- [ ] Reject
- [ ] One generator block; crossed subset disabled
- [ ] Alternative balanced generator pool: _________________________

The block remains `inactive`, weight 0, and unauthorized until implementation after sign-off.

## Decision 3 — confirmatory H1–H4 effects

“Minimum meaningful effect” is the smallest effect worth detecting and is used for design. “Expected effect” is a planning belief. They must be recorded separately.

| Hypothesis | Frozen contrast and endpoint | Unit/direction | Test/effect quantity | Holm treatment | Minimum meaningful effect | Expected effect |
|---|---|---|---|---|---|---|
| H1 | C2 vs C0; binary phishing prediction at frozen threshold | paired phishing `scenario_id`; anticipated recall deterioration but two-sided inference | exact McNemar; `recall(C2)-recall(C0)` | two detectors = 2 of 7 tests | ______ | ______ |
| H2 | `I(C0≠C2)-I(C0≠C1)` at frozen threshold | paired scenario; anticipated larger boundary change for C2 | paired binary test/scenario bootstrap; mean indicator difference | two detectors = 2 of 7 | ______ | ______ |
| H3 | C3 vs C2; binary phishing prediction at frozen threshold | paired phishing scenario; anticipated condition shift, contingent on manipulation check | exact McNemar; `recall(C3)-recall(C2)` | two detectors = 2 of 7 | ______ | ______ |
| H4 | detector-by-transformation response | same scenarios across both frozen detectors; nondirectional | cluster-bootstrap interaction contrast; exact effect scale must be approved | 1 of 7 | ______ | ______ |

All seven p-values use Holm step-down at family-wise alpha 0.05. Transition tables are descriptive support for discordant observations. Standardized probabilities are secondary.

## Decision 4 — phishing power, legitimate precision, and attrition

### Phishing scenarios

Current exact-McNemar/seven-test-Holm sensitivity runs (3,000 simulation design; fixed seed):

| Effect | Discordance | N | Minimum power | Meets 0.80? | Meets 0.90? | Base C0–C3 construction burden |
|---:|---:|---:|---:|---:|---:|---:|
| 0.02 | 0.10 | 500 / 750 / 1,000 | 0.057 / 0.137 / 0.229 | no | no | 2,000 / 3,000 / 4,000 variants |
| 0.04 | 0.10 | 500 | 0.609 | no | no | 2,000 variants |
| 0.04 | 0.10 | 750 | 0.866 | yes | no | 3,000 variants |
| 0.04 | 0.10 | 1,000 | 0.965 | yes | yes | 4,000 variants |
| 0.06 | 0.12 | 500 / 750 / 1,000 | 0.960 / 0.996 / 1.000 | yes | yes | 2,000 / 3,000 / 4,000 variants |

These are sensitivity assumptions, not a selected N. Dependence between hypotheses/detectors and the H4 effect require approval.

### Legitimate controls

Legitimate N estimates specificity/FPR precision; it is not determined by phishing N. Approximate Wilson 95% CI half-widths:

| Legitimate N | specificity 0.90 | specificity 0.95 | specificity 0.98 | C0–C3 variants |
|---:|---:|---:|---:|---:|
| 100 | ±5.96 pp | ±4.51 pp | ±3.23 pp | 400 |
| 250 | ±3.74 pp | ±2.77 pp | ±1.87 pp | 1,000 |
| 500 | ±2.64 pp | ±1.93 pp | ±1.28 pp | 2,000 |
| 750 | ±2.15 pp | ±1.57 pp | ±1.03 pp | 3,000 |
| 1,000 | ±1.86 pp | ±1.36 pp | ±0.89 pp | 4,000 |

- Target power: [ ] 0.80  [ ] 0.90  [ ] other ______
- Approved phishing N: ______
- Expected specificity used for precision: ______
- Required legitimate CI half-width: ______
- Approved legitimate N: ______

### Construction attrition

Freeze before generation: `N_construct = ceil(N_final / (1 - expected_attrition))` separately by population and required complete condition set. Expected attrition is **pending pilot review**. Construction N must never be increased after inspecting detector outcomes.

- Approved expected attrition: ______
- Evidence: pilot reviewed ______ / ______; rejected/incomplete complete sets ______

## Decision 5 — C3 manipulation acceptance

C3 must retain intent and requested action while expressing it less directly. Candidate rules for approval—not yet selected:

| Rule | Candidate threshold | Consequence |
|---|---|---|
| Semantic preservation | 100% of included C2/C3 pairs approved by both reviewers or adjudication | Strong invariant; failures exclude the pair before detector evaluation. |
| Requested-action preservation | 100% of included pairs | Prevents C3 becoming action removal. |
| Ordered explicitness | median paired C2−C3 ≥1 and scenario-bootstrap 95% lower bound >0 | Strong evidence of aggregate manipulation; may require prompt revision/new pilot if it fails. |
| Less-direct pair rate | candidate ≥75%, ≥80%, or ≥90% after aggregation | Higher threshold improves separation but increases pilot failure risk; select before review summary inspection. |
| Entity/channel/safety failures | candidate 0% among included pairs | Appropriate hard safety/invariance gate. |
| Naturalness/condition fit | both reviewers yes or adjudicated approval | Prevents artificial condition artifacts without imposing an arbitrary global score cutoff. |

- Approved ordered-effect rule: _________________________________
- Approved less-direct pair rate: _______________________________
- Approved invariant/safety rule: _______________________________

## Decision 6 — reviewer agreement and pilot execution

- Binary/nominal categorical fields and decisions: ordinary Cohen’s kappa, reported with raw agreement and prevalence table.
- Ordered `yes/uncertain/no` fields if analyzed ordinally: weighted Cohen’s kappa with weights frozen in advance.
- Action-explicitness 1–5: quadratic-weighted kappa is the primary recommendation for two ordinal raters; two-way absolute-agreement ICC may be secondary only if treating the scale as interval is explicitly justified.
- Do not apply ICC to nominal fields.

No universal kappa cutoff is assumed. Candidate operational rules are: require raw agreement plus kappa/weighted kappa to be reported; adjudicate every disagreement; if agreement is too low for reliable rubric use, pause freeze, clarify the rubric, version it, and rerun a detector-blinded pilot rather than averaging unreliable judgments.

Execution order:

1. Reviewer A independently completes every required field using a stable ID.
2. Reviewer B independently reviews the same items without seeing A’s answers.
3. Neither workbook/view contains detector predictions, probabilities, thresholds, or detector-derived selections.
4. Compute agreement and the preregistered aggregate C2−C3 manipulation check.
5. Send only disagreements, uncertain/failing invariants, and manipulation failures to a detector-blinded adjudicator.
6. Preserve original reviews and adjudication as separate audit records.

- [ ] Agreement statistic/weights approved: ______________________
- [ ] Minimum operational agreement rule approved: ______________
- [ ] Two independent reviews completed
- [ ] Adjudication completed

## Decision 7 — final sign-off and transition

- [ ] Decisions 1–6 completed and dated
- [ ] Prompt text/version/hash approved
- [ ] Source manifest contains authorization evidence and hashes
- [ ] Generator assignment manifest approved
- [ ] Pilot manipulation passed
- [ ] `DRAFT_DO_NOT_GENERATE` removal authorized
- [ ] Full frame construction authorized
- [ ] Detector-blinded generation separately authorized

Researcher: __________________ Date: __________  
Faculty mentor: ______________ Date: __________

Until all boxes are complete: `PROMPT_FINALIZABLE=false`, `GENERATION_UNLOCKABLE=false`, `FULL_FREEZE_READY=false`.
