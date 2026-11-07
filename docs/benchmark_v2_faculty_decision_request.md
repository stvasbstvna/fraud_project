# Faculty decision request: Benchmark v2

## Research question

How do controlled wording transformations affect two frozen banking-smishing detectors when semantic intent, requested action, channel, entities, label, and safety state remain fixed?

## Why v2 is needed

Benchmark v1 established an initial paired rewrite workflow. V2 is designed to separate controlled C0–C3 transformations, preserve scenario-level pairing, improve provenance, and preregister a seven-test Holm-corrected analysis before any confirmatory outcomes are observed.

## Completed

The protocol, schemas, validator, C3-softened pilot, review rubric, adjudication procedure, source-manifest specification, generator candidate, exact Holm simulation framework, frozen model hashes, and automated readiness checks exist. Technical integrity checks pass. No v2 generation or detector evaluation has run.

## Why it cannot yet be frozen

Source permissions, final composition, generator approval, meaningful effects/power/N, C3 acceptance criteria, reviewer agreement rules, and the two-reviewer pilot are not approved. Freezing now would silently invent scientific assumptions.

## Decisions requested

1. **Source strategy:** authorized real anchors, researcher-authored synthetic anchors, or a source-stratified hybrid. Hybrid is recommended only if authorization and contamination checks succeed; otherwise synthetic-only requires narrower ecological claims.
2. **Generator:** approve/modify/reject inactive OpenAI `gpt-5.4-mini-2026-03-17`, temperature 0.2, top_p 1.0, no seed claim, one output/job, two bounded retries, 500 tokens, detector context prohibited.
3. **Power:** record minimum meaningful and expected effects for H1–H4, discordance/dependence, target power 0.80 or 0.90, final phishing N, and attrition rule. At effect 0.04/discordance 0.10, sensitivity power is 0.609/0.866/0.965 for N=500/750/1,000.
4. **Legitimate precision:** choose expected specificity and acceptable 95% CI half-width. At N=500 it is approximately ±2.64 pp if specificity is 0.90 and ±1.93 pp if 0.95.
5. **C3 manipulation:** approve semantic/action invariance requirements, aggregate C2−C3 explicitness rule, and less-direct pair-rate threshold.
6. **Agreement:** ordinary kappa for nominal fields; weighted kappa for ordinal fields; optionally ICC only for the 1–5 rating if interval-scale treatment is justified. Approve the action taken when reliability is inadequate.
7. **Pilot:** require two independent detector-blinded reviewers, agreement calculation, then adjudication.

## Freeze implications

Approval fixes the design before generation. It does not authorize detector evaluation. `DRAFT_DO_NOT_GENERATE` remains until the manifest, pilot, prompt hash, assignments, sign-offs, readiness check, tests, and freeze hashes all pass.

## Approval checklist

- [ ] Source strategy/composition
- [ ] Generator/configuration
- [ ] H1–H4 meaningful effects
- [ ] Discordance/dependence and target power
- [ ] Phishing N and legitimate precision/N
- [ ] Attrition rule
- [ ] C3 acceptance rule
- [ ] Agreement statistic/response to low agreement
- [ ] Pilot completion/adjudication
- [ ] Final prompt and freeze transition

Faculty mentor: ____________________ Date: __________
