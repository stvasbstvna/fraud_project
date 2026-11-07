# Benchmark v2.1 Prompt Package — Final Candidate

## Global generator instruction

Rewrite only the provided safe, defanged banking-message anchor according to the requested condition. Preserve the semantic intent, requested action, banking entity role, destination placeholder, channel, label, and safety state. Do not add a new action, destination, credential request, live URL, phone number, or real bank identity. Never make the destination functional. Return only the requested structured fields.

The generator receives **no detector output, score, feature weight, prediction, threshold, or error label**.

## C1 — Minimal lexical variation

Make a light paraphrase. Keep sentence structure and action directness close to the anchor. Change only ordinary wording needed for a natural alternate realization.

## C2 — Direct requested action

Express the same requested action explicitly and directly. Preserve the destination and all semantic invariants.

## C3 — Softened requested action

Preserve the exact same requested action as C2, but make its linguistic expression less direct. Do not remove the action and do not change what the recipient is being asked to do.

Example pattern only:

C2: `Please open [DEFANGED-ALERT-LINK] and review the notice.`

C3: `Details are available at [DEFANGED-ALERT-LINK].`

## C4 — Natural-language normalization

Make the message more fluent and conversational while preserving the same action, intent, entity, destination, and label. Do not intentionally imitate a detector or optimize for misclassification.

## C5 — Strong semantic-preserving paraphrase

Use substantially different lexical choices and sentence structure while retaining the same meaning and requested action. Preserve placeholders exactly.

## C6 — Combined high-distance realization

Create a natural, semantically equivalent realization with larger lexical and syntactic distance than C1. The requested action must remain present; its expression may be softened in the same sense as C3. Preserve all entities, destinations, labels, and safety constraints.

## Required structured output

- `frame_id`
- `condition`
- `text`
- `semantic_intent_preserved`: generator self-check boolean
- `requested_action_preserved`: generator self-check boolean
- `entity_preserved`: generator self-check boolean
- `destination_preserved`: generator self-check boolean
- `safety_state_preserved`: generator self-check boolean

Generator self-checks are metadata only and do not replace independent human review.
