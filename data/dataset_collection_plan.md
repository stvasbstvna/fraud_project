# Dataset Collection and Separation Plan

No final banking-filtered dataset currently exists in this repository. The folders under `data/` are placeholders and raw files are ignored by Git.

## Common schema

Required fields are `message_id`, `pair_id`, `source_id`, `source_record_id`, `text`, `subject`, `channel`, `authorship`, `generation_type`, `generator`, `prompt_version`, `banking_label`, `banking_subtype`, `class_label`, `requested_action`, `split_group`, `split`, `license_note`, and `provenance_note`.

## Separation rules

### Human versus AI

- `human`: documented human-origin message or source corpus. Unknown origin remains `unknown`, not human by default.
- `ai_written`: generated without a specific human source message.
- `ai_rewritten`: linked to a source message through `pair_id` and reviewed for preserved intent/action.
- Generator and prompt metadata are stored separately. Human versus independently generated comparisons are secondary; the primary result uses paired rewrites.

### Banking versus non-banking

Use a high-recall candidate filter, followed by manual review. A message is banking-related when it impersonates or discusses a bank, credit union, card issuer, payment/transfer service acting like an account provider, bank account, card, transfer, ATM, loan, or banking credential. Generic prizes, parcel delivery, cryptocurrency promotions, and unrelated invoices are non-banking unless a banking institution/account is central to the pretext.

Record `banking_yes`, `banking_no`, or `uncertain`, plus a subtype. Keyword hits alone do not establish the final label.

### Channel

Use `sms`, `email`, or `other_text`. Preserve email subject and body separately before creating a combined text field. Do not infer a channel from message length. Analyze each channel separately before any pooled result.

### Scam versus legitimate

- `phishing_scam`: deceptive impersonation or pretext asking for an action that can transfer value, credentials, access, or control.
- `legitimate`: verified benign/transactional message under the source's labeling process.
- `spam`: unsolicited promotion without deceptive impersonation; keep separate where supported.
- `uncertain`: insufficient evidence or conflicting labels; excluded from primary training until adjudicated.

## Collection sequence

1. Record source URL, version/date, checksum, terms, citation, and original schema.
2. Obtain data from its original source where possible; do not treat the uploaded archive as proof of redistribution permission.
3. Store raw files under `data/raw/<source_id>/` locally.
4. Normalize without overwriting raw data and retain source record IDs.
5. Redact unnecessary personal information and defang URLs.
6. De-duplicate exact normalized text, then inspect near duplicates.
7. Run the banking candidate filter and perform blinded human review.
8. Freeze grouped splits. Group by source record, near-duplicate cluster, thread/campaign when known, and rewrite family.
9. Generate and review rewrites only within their assigned split.
10. Write a dataset card with counts, exclusions, agreement, class balance, hashes, and limitations.

## Banking filtering plan

The starter filter in `src/banking_filter.py` produces candidates and matched terms. Two annotators should review a pilot where feasible. Disagreements are adjudicated using the message's claimed entity, financial object, requested action, and context. Report precision/recall estimates for the filter on a random sample and on all excluded source strata. Until this work is complete, use the phrase “banking candidates,” not “banking dataset.”

## Leakage controls

- Split before rewriting and keep each `pair_id` in one split.
- Fit vectorizers, thresholds, and calibration only on training/validation data.
- Remove templates and near duplicates across splits.
- Keep an untouched test set; mitigation training cannot use its rewrites.
- Report source-held-out and generator-held-out checks if sample size permits.
