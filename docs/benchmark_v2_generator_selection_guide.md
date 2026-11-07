# Choosing a generator for Benchmark v2

## The correct selection criterion

Choose a generator for **documentability, controlled access, safety/schema compliance, cost, and reproducibility**. Do not choose one because it writes “better scams,” appears more realistic after detector testing, or produces lower recall.

## Options

| Route | Appropriate use | Strength | Limitation | Recommendation |
|---|---|---|---|---|
| Versioned API model | Final generation after protocol freeze | Exact model ID, structured output, easy logging | Costs money; model availability can change | Preferred if budget permits and exact version/settings are recorded |
| Local open-weight model through Ollama | Pilot or final work only if hardware/version are fully documented | Privacy, no per-request cost, reproducible local runtime | Hardware quality/latency; model version and quantization must be frozen | Viable only after a small detector-blinded pilot validates schema compliance |
| Manual ChatGPT web UI | Brainstorming of non-operational scenario frames only | Accessible | Weak logging and version control; cannot guarantee fixed parameters | Do not use as final benchmark generator |
| Multiple-generator pool | Robustness check against generator-specific style | Tests whether one generator causes the result | More review and balancing work | Use only if scenario-level stratified assignment and sample size support it |

## Provider decision gate

Before selecting a provider/model, answer yes to all questions:

1. Can we record an exact model/version (or local model file/quantization hash)?
2. Can we retain the exact prompt/version and settings?
3. Can it reliably return the schema without producing operational phishing details?
4. Can it be assigned before detector execution and balanced across conditions?
5. Can the project afford enough calls for candidates, rejections, and the approved final set?

If any answer is no, use the tool only for non-final brainstorming, not confirmatory generation.

## Practical route for this project

1. Do **not** reuse the exhausted v1 API process for v2 until the v2 protocol is frozen.
2. Use a small, detector-blinded pilot to compare operational viability of up to two candidate generators, not detector degradation.
3. Freeze either one generator or a balanced pool after reviewing pilot cost, schema pass rate, human-review pass rate, and documentation quality.
4. Assign generator blocks at scenario level. The same scenario’s lineage must obey the protocol’s generator rules.
5. Keep a separate optional fully-crossed subset only if planned in advance; it does not create extra independent scenarios.

## What to request from a generator

Request one safe, structured candidate from a semantic frame; require placeholders and defanged URLs; require JSON; reject violations automatically; then human-review the candidate.

Never request: live destinations, credentials, payment steps, real victim personalization, real bank impersonation details, or content designed to bypass a named detector.

