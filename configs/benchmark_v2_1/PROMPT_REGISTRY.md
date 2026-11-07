# Exact prompt registry — canonical-v1

C0 is the unchanged defanged source anchor; no LLM transformation. These prompts are prepared but have NOT been executed. Archived flat prompt packages are not used by this pipeline.

| Condition | Prompt version | Purpose / allowed transformation | Forbidden |
|---|---|---|---|
| C1 | canonical-v1 | Change only a small number of ordinary words. Preserve sentence structure and action directness as closely as possible. | Any changed invariant, added fact or functional endpoint |
| C2 | canonical-v1 | Express the existing requested action clearly and directly. Do not add an action or strengthen the consequences. | Any changed invariant, added fact or functional endpoint |
| C3 | canonical-v1 | Express the existing requested action less directly. The reader must still be asked to perform that same action. Merely saying that information is available does not satisfy this condition. | Any changed invariant, added fact or functional endpoint |
| C4 | canonical-v1 | Improve grammar, fluency, natural phrasing and awkward formatting. Retain the existing meaning, requested action and level of urgency. | Any changed invariant, added fact or functional endpoint |
| C5 | canonical-v1 | Use substantially different vocabulary, syntax, phrase structure and sentence structure. Preserve all controlled semantic variables. | Any changed invariant, added fact or functional endpoint |
| C6 | canonical-v1 | Make the largest safe surface-language transformation you can using vocabulary, syntax, organization and style, while preserving every controlled semantic variable. Do not invent new context to increase distance. | Any changed invariant, added fact or functional endpoint |
