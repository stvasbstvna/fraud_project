# Automated pilot protocol — version 1

Declared before automated semantic review or any detector scoring. This separate branch uses `review_mode=automated`, `validation_type=automated_semantic_review`. It does not change human-review decisions, old gates, existing generation prompts/configuration, models or historical results. The user explicitly authorized a reduced **balanced** cohort and machine semantic validation for this branch.

## Roles, identity and independence limits

- Generator: existing exact `gpt-5.4-mini-2026-03-17`; temperature 0.2, top_p 1, seed null, one C1–C6 output per frame/condition, maximum 500 output tokens, existing exact `canonical-v1` prompts unchanged.
- Reviewer A: `gpt-5.4-mini-2026-03-17`.
- Reviewer B: `gpt-4.1-mini-2025-04-14`.
- Adjudicator: `gpt-4.1-2025-04-14`.
- Review temperature 0, top_p 1, seed null, maximum 1,200 output tokens. Reviewer B receives the same source/variant input in an isolated call and does not see A. Adjudication explicitly receives A/B outputs. Calls are independent contexts and use different snapshots, but share a provider and may share biases; no claim of statistically independent errors or human expertise is made.

Exact role prompts, structured schemas and parameters are materialized in `configs/benchmark_v2_1/automated_pilot/` before execution. Provider metadata access was checked for all three snapshots, and the generator completed a neutral structured-output probe; access is verified rather than assumed. No silent fallback is permitted. Exact raw requests/responses, hashes, model IDs, usage, timestamps and attempts are retained in the separate call cache. SDK automatic retries are disabled; at most two logged technical attempts, zero semantic regeneration. Numeric facts/placeholders are fixed. Requests contain no predictions, thresholds, feature weights or evaluation feedback.

## Sources and deterministic validation

Inspect the entire previously audited candidate pool, every distinct viable negative-control family, and registered locally available sources. Keep unresolved licenses/provenance HOLD, including upstream-rights uncertainty for local SmishX; no ordinary personal SMS or email/multilingual rows fill quotas. Existing source labels are candidate evidence, not guaranteed truth. No new source messages are authored.

Retain `pilot-template-v2` thresholds and normalization. Propagate train/validation contamination to its candidate template component conservatively. One representative per family, with candidate negatives preferred when the same component includes multiple source copies. All deterministic exclusions are recorded as rule-based decisions, distinct from final semantic approval.

English, SMS length/channel, financial relevance from prior source screening, safety, provenance, local-use license and source label availability must pass. Review all surviving control families and the first 24 distinct positive families in deterministic order; if too few positives are approved to match controls, inspect additional positive families without using detector information. Reject source encoding damage and unsupported annotations. Require an existing requested action; `NONE` actions cannot support C2/C3, so purely informational messages are not forced into this design. Entity/destination may be `NONE` only when genuinely unspecified, remaining unspecified through rewriting.

## Semantic source/rewrite decisions

Subjective confidence threshold is fixed at **0.80**, not tuned against detector results. A/B source decisions must agree on relevance, safe status, label and compatible controlled annotations. Exact normalized annotation agreement may be approved directly; nonidentical/discordant annotations are resolved by a third semantic pass. Uncertainty is rejected. Different labels supplied by reviewers are retained as disagreements, not silently overwritten with the source label. Semantic confidence is uncalibrated machine judgment.

Each generated variant first passes safety, all bracketed placeholders (including numeric tags), numeric-fact, literal entity and destination checks. Then two blind machine passes judge intent/action/entity/destination/label preservation, condition compliance, no new facts, naturalness and safety. A disagreement can be adjudicated; unresolved or agreed invalid outputs fail. No best-of selection or semantic retry. A failed condition excludes the whole frame from primary complete cases.

## Cohort, freeze and inference

Choose the largest balanced cohort up to 24/24 among approved unique families, with no source exceeding half the cohort, via an exact label/source-capacity flow. Choose diversity of entity/category without scores within allocated source cells. Repeat balance selection among complete approved frames **before scoring**; report every lost frame and condition. Reduced sample sizes are explicitly exploratory, not represented as the planned 1,250-frame confirmatory benchmark.

Compute distance using the existing fitted vectorizers and existing equal-weight surface-distance formula. Prespecified manipulation checks require at least 80% paired C1<C5 and C1<C6; directness is checked by two isolated comparisons of actual C2/C3 text. Do not force monotonicity. Failed manipulation is recorded, with any frozen/evaluated output explicitly exploratory and unsuitable for confirmatory interpretation.

Freeze safe complete rows, cohort/label/source/family counts, all prompt/config/review/model hashes and validation type. Never mark them human approved. Reuse unchanged LR/RF and threshold .5 without fitting. Primary paired slopes and five contrasts retain the existing seven-member two-sided Holm family; frame bootstrap 10,000 draws, seed 42. Model-specific signed/absolute distance associations and LR/RF comparisons are exploratory frame-level summaries, not row-independent significance tests. Insufficient/zero-variance cases remain unavailable rather than fabricated.

Eight tables and five figures come from the same frozen complete cases. The primary example is nearest median frame-mean absolute movement with stable-ID ties; extremes are separate. Every report must disclose automated semantic review rather than independent human annotation, shared model/provider bias, reduced N, complete-case attrition and manipulation failures. Low N or machine consensus cannot establish universal detector robustness, practical safety or lexical causality.
