# Human review protocol

Current state: 441 C0 candidate texts, 882 blank review assignments, zero approvals. No generated rewrite exists. Reviewers must not receive detector probabilities, predictions, weights or misclassification status.

## Source review comes first

Check actual source evidence, English SMS channel, banking relevance, malicious/legitimate intent, original label semantics, requested action, entity, destination, facts and license/provenance. Do not approve ordinary bank notices as malicious just because the CSV label says phishing. Existing `intent` and `requested_action` fields are hypotheses to check, not answers to copy. If context is insufficient, mark pending or needs_adjudication. Any source-text change requires a new content-derived frame ID; preserve the old candidate and review record.

`review/source_review_queue.csv` contains 882 source-level assignments separate from the 882 C0 variant assignments. A `source_sha256` digest binds all source metadata except mutable review status/notes, including action, intent, label and provenance. `review_sources --reviews COMPLETED.csv` imports actual independent decisions into a new reviewed source file; missing or conflicting decisions stay pending. Copying `review_status=approved` into a generation CSV is insufficient: request export and freeze require the independent source review evidence too.

## Variant review

Two independent reviewers each record `approved`, `rejected`, `needs_adjudication`, or `pending`. Every approval requires `yes` for semantic/action/entity/destination/label/intent/channel/facts/safety preservation, naturalness and condition compliance; `no` or missing blocks freeze. Numeric directness ratings can support C2 versus C3; they are not inferred from the condition name. `text_sha256` binds a decision to exact text; changed text needs fresh review. Reviewer identifiers must be distinct and nonblank. All raw individual decisions are retained; automated checks cannot fill them.

Disagreement goes to the adjudication CSV with a third person's decision/reason. The conservative current gate requires independent approvals after resolution; adjudication alone does not overwrite or erase a rejection. Complete independent re-reviews of the corrected variant are kept in a new review artifact. Cohen's kappa is appropriate for categorical preservation decisions; weighted kappa only for ordered directness ratings. Agreement is NOT AVAILABLE until actual ratings exist.

## Pilot and manipulation validation

Use the distinct candidate pilot (24/24) only after source eligibility. Review preservation, naturalness, C1 minimal change, C3 same action but less direct than C2, and C6 high surface change. Prospectively require ≥95% semantic/action preservation, ≥98% entity/channel/safety preservation and ≥80% C3 less-direct judgments (from the existing planning assumptions); record denominators and uncertainty. Automated distance stage requires at least 80% paired C1<C5 and C1<C6. Any threshold failure is a design problem, not permission to filter by detector results. Revisit these planning thresholds prospectively if source design changes.

Before freeze, `review/pilot_validation.json` must record explicit human signoff fields `semantic_action_valid`, `directness_valid`, `agreement_adjudicated`, `attrition_rule_frozen` plus SHA-256 `review_file_sha256` of the reviewed file. This is an external evidence artifact, not automatically generated approval. Full-scale confirmatory use still requires independent source families and an actual sampling/attrition plan; meeting a file/schema gate is not scientific signoff.

## Operational handling

Review queue rows contain safe text and semantic fields only; no detector results. Never open links from source messages. Preserve placeholders and use the fixed safe baseline in C0. New domains, emails, phones, IPs, credential/payment endpoints or lost placeholders block objective validation. Human review must also catch obfuscated addresses, names/PII, unsupported claims and unsafe details a regex can miss.
