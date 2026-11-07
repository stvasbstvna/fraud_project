# Paired LLM rewrite protocol

## Primary condition

- Condition: `T1_llm_neutral_rewrite`
- Model: `gpt-5.4-mini-2026-03-17`
- API: OpenAI Responses API
- Reasoning effort: none
- One rewrite per frozen banking-test message
- No detector prediction, probability, vocabulary, or feedback is supplied to the model

The fixed snapshot is used so that the generator can be reported and reproduced. The model is a data-transformation instrument, not a detector and not a source of ground-truth labels.

## Prompt

> You are transforming a DEFANGED SMS example for a controlled academic robustness study. Rewrite it once in natural contemporary SMS language. Preserve the same high-level situation, true class, semantic intent, and requested-action category. Keep every bracketed placeholder exactly as written. Keep any defanged destination non-operational. Do not add a real URL, phone number, email address, personal data, credential request, payment instruction, targeting detail, new urgency, threat, reward, or persuasive strategy. Do not optimize against a detector. Do not infer or discuss detector features. Return only the requested structured object.

The row-specific input contains the true class, high-level intent category, requested-action category, and defanged source text.

## Required review

Every generated row starts with `human_review_status=pending`. Before final reporting, a reviewer must confirm:

1. the true class is unchanged;
2. semantic intent is preserved;
3. the requested-action category is preserved;
4. no new operational detail was added;
5. placeholders remain defanged;
6. the rewrite is not identical to the source.

Rejected rows must be regenerated without using detector feedback. The primary analysis includes only rows marked `approved`.
