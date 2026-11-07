# Benchmark v2 project status

Updated: 2026-08-28. This is an evidence-based repository status, not an authorization to generate or evaluate Benchmark v2.

## Existing and complete

- Benchmark v1 data, frozen TF–IDF logistic-regression and random-forest artifacts, v1 rewrite results, and approved human-review records remain separate from Benchmark v2.
- Benchmark v2 has a protocol, hypotheses, seven-test Holm analysis family, schemas, validator, review rubric, generation/review runbook, provenance specification, pilot builder, and tests.
- The non-operational pilot contains 48 researcher-authored frames, 192 unique C0–C3 variants, and 144 jobs marked `not_run`; none is eligible for final detector evaluation.
- C3 is consistently implemented in active files as a softened, less-direct expression of the same C2 requested action. It is not removal or replacement of the action.
- A detector-blinded pilot workbook and adjudication protocol exist.
- An exact conditional-binomial McNemar simulation framework applies Holm step-down correction jointly to seven tests. Current output is sensitivity analysis, not a frozen sample-size determination.
- A strict offline readiness checker now separates technical readiness from full readiness.

## Incomplete or blocked

- The prompt package remains a draft and the freeze register remains `DRAFT_DO_NOT_GENERATE`.
- No generator block is active. Provider, model, exact version, and verified seed behavior require an explicit selection.
- The only current source-manifest row describes the researcher-authored pilot. It does not authorize final generation or redistribution, and final authorized anchors have not been supplied.
- The baseline audit found 49 critical TBD/decision markers. Objective resolutions reduced the active blocking marker count to 19; they are enumerated in `results/benchmark_v2/freeze_readiness.json` and collapsed into decision families in the decision matrix.
- Final power assumptions (minimum effects, discordance, dependence, complete-set attrition, and target-power criterion) have not been approved.
- Pilot human judgments and second-reviewer/adjudication results are incomplete. No decision has been fabricated.
- Consequently there is no full benchmark, final review set, final analysis-ready dataset, confirmatory detector evaluation, or confirmatory result.

## Human action required

The smallest decision set is maintained in `docs/benchmark_v2_required_decisions.md`: generator selection; authorized final sources and usage evidence; confirmatory power assumptions; C3 aggregate manipulation threshold and ordinal agreement statistic; reviewer completion/adjudication; and formal freeze sign-off.

## Automatically completed work

Repository consistency checking, pilot integrity and checksum verification, candidate generator schema, pilot source declaration, exact Holm simulation software, sensitivity outputs, and adjudication rules can be completed without making scientific choices. Those artifacts do not turn candidate values into confirmatory assumptions.

## Consistency and stale-language audit

Active Benchmark v2 configuration, protocol, prompt draft, pilot builder, pilot outputs, review instructions, and tests use the approved C2-direct/C3-softened direction. Historical freeze snapshots may retain superseded wording and are deliberately labeled draft/snapshot provenance; they must not be treated as current instructions. Generic discussions of semantic-change rejection or evasive attacks elsewhere in Benchmark v1 are not C3 definitions and were not rewritten.

## Current gate

`TECHNICAL_FREEZE_READY_HUMAN_DECISIONS_PENDING` may be reported when all software/integrity checks pass. `FULL_FREEZE_READY` and generation authorization must remain false until every scientific/provenance/review blocker is resolved. Downstream phases must not run early.
