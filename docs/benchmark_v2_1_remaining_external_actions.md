# Remaining external actions that cannot be fabricated by the repository

The automated project package now fixes the research-owned design decisions and prepares all code paths. Two operations still require resources outside an offline repository session:

1. **Independent human review.** Two people must complete the pilot/final review forms. Software cannot legitimately fabricate these judgments and label them human review.
2. **Authorized LLM generation.** The configured generator must be called from the researcher's environment after the freeze gate passes. The repository must not substitute rule-based text and call it LLM output.

After these are completed, the included scripts can build the final analysis-ready benchmark and run the frozen detector/statistical pipeline.
