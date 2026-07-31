# Banking and Finance Filtering Plan

## Purpose

The filter creates a high-recall review queue. It does not establish that a message is banking-related. A row is marked `is_banking_candidate=true` only when its text matches at least one configured term as a whole word or phrase, case-insensitively.

## Exact filter list

`bank`, `account`, `card`, `credit`, `debit`, `payment`, `transaction`, `transfer`, `deposit`, `withdrawal`, `balance`, `fraud`, `security`, `suspicious`, `locked`, `suspended`, `verify`, `login`, `password`, `OTP`, `code`, `PayPal`, `Zelle`, `Venmo`, `Cash App`, `Chase`, `Wells Fargo`, `Bank of America`, `Capital One`, `Citi`, `Discover`, `American Express`, `Stripe`.

Matches are saved in `banking_keyword` in this order, separated by `|`. Named brands from the list are also copied to `brand_mentioned`.

## Current automatic results

| Source | Total rows | Candidate rows |
|---|---:|---:|
| SmishX | 1,200 | 173 |
| Cross-model human phishing | 5,000 | 1,914 |
| Cross-model LLM phishing | 4,986 | 4,285 |
| **Committed total** | **11,186** | **6,372** |

The high LLM candidate count is expected because the generation categories and prompts frequently use account, security, verification, and code language. It does not mean all 4,285 rows are banking attacks.

## Manual review procedure

Review `banking_manual_review.csv` without changing the source label. For each row, set:

- `manual_banking_related=yes` when a bank, card issuer, banking/payment account, transfer, deposit/withdrawal, or named financial service is central to the message.
- `manual_banking_related=no` when the match is incidental or clearly belongs to another domain. Examples include source code, a generic security code for a nonfinancial account, greeting-card content, or credit used in a nonfinancial sense.
- `manual_banking_related=uncertain` when the institution or financial object cannot be determined from the text.

Use `manual_notes` to record the decisive phrase and any ambiguity. A brand match is supporting evidence, not an automatic `yes`.

## Review order and quality control

1. Pilot 200 stratified candidates across source, channel, label, and authorship.
2. Have two reviewers label the pilot independently when possible.
3. Discuss disagreements and revise examples before the full pass.
4. Calculate agreement and candidate precision overall and by source.
5. Audit a random sample of non-candidates to estimate missed banking messages.
6. Create final banking subsets only from `manual_banking_related=yes` rows. Until then, filenames with `banking_` contain candidates, not final banking labels.

## Human and AI separation

The current `banking_human_written.csv` and `banking_ai_generated.csv` are candidate subsets based on source-supported authorship. SmishX candidates are absent from both because authorship is unknown. `banking_ai_rewritten.csv` is header-only because no license-cleared AI-rewrite source is currently available. These files must be filtered again by manual review before being called final banking datasets.

## Requested action and intent

The builder uses conservative text rules for explicit credential provision, money transfer, account verification, link navigation, phone/reply contact, and attachment actions. Unmatched rows remain `unknown`. These fields help prioritize review; they are not human ground truth and must not be used as if manually annotated.
