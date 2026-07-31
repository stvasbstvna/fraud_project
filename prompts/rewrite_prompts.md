# Controlled Rewrite Protocol

These prompts are for offline defensive research on already-labeled samples. They are not for live delivery or targeting.

## Rewrite instruction (version `rewrite_v1`)

Given a redacted banking scam message from the training or test benchmark, produce one text-only paraphrase for robustness evaluation. Preserve the claimed situation, institution category, requested user action, and malicious intent. Change wording, tone, grammar, and formatting naturally. Do not add personal data, working links, phone numbers, credentials, malware, new instructions, or a more effective attack strategy. Replace destinations with `[URL]`, `[PHONE]`, or `[EMAIL]`. Return only the paraphrase.

## Reviewer checklist

- Same banking pretext and requested action?
- No new facts, pressure, reward, threat, or targeting detail?
- No live destination or personal information?
- Meaningful surface rewrite rather than a near-copy?
- Safe to retain as a redacted research sample?

Reject and regenerate or exclude any output that fails a check. Record prompt version, model/version, date, parameters, source `message_id`, output hash, and reviewer decision in `prompt_log.csv`.
