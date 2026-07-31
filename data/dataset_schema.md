# Standardized Dataset Schema

Every processed dataset uses the same 17 columns in this exact order.

| Column | Meaning | Allowed or expected values |
|---|---|---|
| `id` | Stable source-and-row hash identifier | nonempty string; not a source account ID |
| `text` | Normalized message text | whitespace collapsed; URLs defanged; email/phone-like identifiers redacted |
| `label` | Source-supported message class | `phishing`, `legitimate`, `spam`, `unknown` |
| `channel` | Communication channel | `sms`, `email`, `webpage`, `unknown` |
| `source_dataset` | Dataset-level provenance | e.g. `SmishX`, `cross_model_human`, `cross_model_llm` |
| `source_type` | Source/authorship family | descriptive controlled string documented below |
| `is_human_written` | Source-supported human authorship | `true`, `false`, `unknown` |
| `is_ai_generated` | Source-supported AI generation | `true`, `false`, `unknown` |
| `is_ai_rewritten` | AI rewrite linked to a source message | `true`, `false`, `unknown` |
| `is_banking_candidate` | Keyword filter result, not final label | `true`, `false` |
| `banking_keyword` | All matched terms in configured order | pipe-delimited terms or blank |
| `brand_mentioned` | Matched named payment/banking brands | pipe-delimited brands or blank |
| `requested_action` | Conservative rule-based action extraction | `provide_credentials`, `transfer_money`, `verify_account`, `click_link`, `call_phone`, `reply`, `download_attachment`, `unknown` |
| `intent_type` | Rule-based action family | `credential_theft`, `financial_transfer`, `account_verification`, `link_navigation`, `contact_request`, `attachment_action`, `unknown` |
| `has_url` | Whether a URL was extracted before defanging | `true`, `false` |
| `url` | Extracted URL value(s) | pipe-delimited and defanged; blank if absent |
| `notes` | Provenance that does not fit another field | generator/category, upstream source, original label, or uncertainty |

## Authorship rules

- `true` is used only when the source documentation or field explicitly supports the claim.
- SmishX rows are `unknown` for all three authorship flags because the dataset labels message class, not authorship.
- Cross-model human rows are human-written; cross-model LLM rows are AI-generated and explicitly not paired rewrites.
- A message is not AI-rewritten merely because an LLM generated it. A rewrite needs a source link such as `Original_ID` or `pair_id` and source documentation describing rephrasing.

## Labels and derived fields

Source labels are mapped without inventing ground truth: SmishX `smishing` becomes `phishing`, `legitimate` remains `legitimate`, and `spam` remains `spam`; both cross-model source files are documented as phishing-only. Banking, brand, URL, requested-action, and intent fields are deterministic rule outputs. They are screening features, not manual annotations.

## URL safety

Committed message text and the `url` field replace `http` with `hxxp` and dots with `[.]`. Email addresses and phone-like identifiers are replaced with `[EMAIL]` and `[PHONE]`. This preserves analyzable structure without publishing clickable links or obvious contact identifiers. No network request is made to any message URL.

## Manual review schema

`banking_manual_review.csv` uses the requested columns:

`id,text,label,channel,source_dataset,banking_keyword,is_banking_candidate,manual_banking_related,brand_mentioned,requested_action,intent_type,manual_notes`

`manual_banking_related` and `manual_notes` are blank by design. Reviewers should enter `yes`, `no`, or `uncertain` only after reading the message under the annotation guidance.
