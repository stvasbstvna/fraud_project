# Benchmark v2 decisions still requiring explicit signoff

Only decisions that cannot be inferred safely are listed here. Other protocol details are already implemented or can be completed automatically.

## 1. Generator block

Approve or replace the inactive candidate: OpenAI `gpt-5.4-mini-2026-03-17` through Responses strict structured output. This exact snapshot is recommended because it is already recorded in the repository's v1 rewrite tooling, not because of detector outcomes. Use one documented primary block; add a second only if budget permits balanced scenario-level assignment.

Required values: provider, model identifier, exact snapshot/version, supported seed behavior, temperature approval, budget, assignment weights, and whether the optional crossed-generator subset is enabled.

## 2. Final anchor-source authorization

Choose one basis:

- **Researcher-authored synthetic anchors (recommended for redistribution safety):** project owner explicitly authorizes research generation and public examples.
- **Transformed real anchors:** provide source URLs/files plus redistribution and transformation permission.
- **Mixed:** freeze proportions and authorization for every source.

The existing pilot manifest is pilot-only and cannot authorize the final benchmark.

## 3. Confirmatory power assumptions

Approve or replace the minimum meaningful paired recall difference, discordant-pair rates for H1/H2/H3/H4, H4 interaction effect, complete-set attrition, target power, and specificity precision target. Current outputs are sensitivity analyses, not a final power justification.

Recommended starting values for faculty review: 4 percentage-point minimum paired recall difference, 10% discordance, at least 80% marginal power, FWER 0.05 with Holm across seven tests, 750 phishing and provisionally 500 legitimate final scenarios. The quality-validation count and construction inflation must be set after approving the complete-set attrition rule. Under the current sensitivity simulation, N=750 gives minimum marginal power about 0.866; this is not a final power freeze.

## 4. C3 manipulation threshold and ordinal agreement

Freeze the minimum acceptable aggregate C2-minus-C3 explicitness difference and select weighted Cohen’s kappa or ICC for ordinal inter-rater agreement. Recommended: median C2−C3 difference at least 1 point, with a positive scenario-bootstrap 95% lower confidence bound; use two-way absolute-agreement ICC when the same reviewers rate all sampled variants, otherwise quadratic-weighted kappa.

## 5. Prompt and protocol signoff

After decisions 1–4, approve prompt package version, exact hashes, protocol version, and removal of `DRAFT_DO_NOT_GENERATE`. This signoff authorizes only detector-blinded quality generation—not confirmatory detector evaluation.

## 6. Human pilot review

Two blinded reviewers must complete the updated C3-softened pilot workbook. Missing decisions, disagreements, preservation failures, or an unsuccessful aggregate C3 manipulation check prevent full freeze.
