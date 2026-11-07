# Prompt design

Exact UTF-8 prompt files are in `configs/benchmark_v2_1/prompts/`; see `PROMPT_REGISTRY.md`. New version: `canonical-v1`. They have been materialized, **not executed**. Archived `docs/benchmark_v2_1_prompt_package_FINAL.md` and flat runner remain unchanged and are not the new registry.

C0 is identical to `defanged_text`, retaining `original_text` for provenance. C1 permits minimal lexical substitutions; C2 makes the same action direct; C3 makes the same action indirect but still present; C4 normalizes language; C5 strongly paraphrases; C6 seeks large safe surface change. C2/C3 differ in directness, not necessarily measured distance. No categorical index is assumed to be a numeric dose.

Every prompt explicitly controls label, intent, action, literal entity, destination, channel, facts and safety; forbids new facts/operational details; preserves placeholders including multiplicity; requires JSON `{frame_id, condition, text}`. We removed the old potentially action-removing C3 example. Self-reported semantic preservation is not requested as approval evidence.

Payload construction uses an allowlist. Generator requests contain no detector scores, predictions, features, weights, threshold or results. Exact prompt and full request hashes accompany request manifests and accepted external responses. Detector-space linguistic measurements stay downstream from generation; no score-based retries or best-of selection. Inherited candidate model is `gpt-5.4-mini-2026-03-17`; availability/access is NOT VERIFIED. No provider substitution is permitted. Seed is null (support not assumed); exact reproduction of a stochastic provider response cannot be guaranteed by temperature alone. Preserve raw request/response envelopes and attempt logs.

The current adapter exports eligible requests and ingests external structured responses; it deliberately does not initiate provider calls. With zero eligible source frames, the dry run exports zero requests. Live provider execution remains a documented external pending action, not a hidden claim of completion.
