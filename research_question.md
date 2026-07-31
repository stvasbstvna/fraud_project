# Research Question and Scope

## Question

Can AI-rewritten banking scam messages bypass phishing detectors more effectively than human-written scam messages, and what mitigation strategies can reduce this detection gap?

## What is being compared

The main comparison is detector behavior on human-written banking scam text and controlled AI rewrites of the same underlying messages. A rewrite should keep the impersonated banking context, requested user action, and malicious intent while changing surface cues such as grammar, tone, urgency, formatting, and obvious scam wording.

AI-written messages without a human source can support a secondary analysis, but they are not equivalent to paired rewrites and will be reported separately.

## Boundaries

- Channels: SMS, email, and comparable text-message channels.
- Domain: retail banking, payment cards, transfers, account access, fraud alerts, and closely related financial-service impersonation.
- Labels: phishing/scam, legitimate, and optionally spam as a separate exclusion or comparison class.
- Primary outcome: false-negative-rate increase from human-written to AI-rewritten scam messages.
- Excluded: Smishing-4C, live phishing campaigns, webpage generation, and sending test messages to real users.

## Unit of analysis

The preferred unit is a pair: one source scam message and one rewrite with a stable `pair_id`. Dataset source, channel, authorship, banking relevance, label, generator, prompt version, and split assignment must remain attached to every row.

## Claims this study can and cannot make

The study can estimate detector robustness within the collected benchmark and rewrite protocol. It cannot claim that all AI phishing is harder to detect, that every channel behaves the same way, or that a benchmark result equals performance in live banking systems.
