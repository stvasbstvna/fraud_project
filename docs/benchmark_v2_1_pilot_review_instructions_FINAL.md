# Benchmark v2.1 Pilot Review Instructions

Two reviewers independently review the 48-frame pilot. Reviewers must not see any detector predictions, confidence scores, feature weights, or model-error labels.

For every variant, record:

1. `semantic_same` — yes/no
2. `requested_action_same` — yes/no
3. `entity_preserved` — yes/no
4. `channel_preserved` — yes/no
5. `destination_preserved` — yes/no
6. `safety_valid` — yes/no
7. `natural_language` — yes/no
8. `directness_rating` — 1 (very indirect) to 5 (very direct)
9. `approve` — yes/no
10. `rejection_reason`
11. `notes`

For C3 and C6, compare the directness rating with C2 from the same frame. The softened condition must preserve the same action rather than delete it.

Pilot acceptance criteria are defined in `benchmark_v2_1_protocol_FINAL_CANDIDATE.md`.
