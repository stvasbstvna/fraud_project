# Source review amendment v3.1 — before any research fitting/scoring

The original v3.0 source prompt's `safe` boolean was ambiguous. Actual A/B outputs on the positive packet labeled almost all phishing candidates as phishing but set safe=false to mean malicious. The implementation intended inert export safety. Consequently the v3.0 gate approved no phishing and cannot be used as the final label-review run. Its requests, raw responses, decisions and summary remain preserved.

The v3.1 prompt/schema explicitly separate `nonoperational_text` (no live operational endpoints/private IDs) from the phishing/legitimate label. A defanged malicious message may pass export safety. The source sample, confidence threshold, model snapshots, financial exclusions and future splits remain fixed. Both controls and positive packets are reviewed afresh; old false safety fields are not silently reinterpreted or converted into approvals. Exact new schema/prompt is saved in `configs/benchmark_v3/source_review_v3_1.json` before these calls.

This corrects a measurement-instrument ambiguity before any research detector was fitted or scored. It is not a response to detector accuracy, significance or a desired threshold crossing. All earlier calls still count in the experiment's execution/cost audit. ModernBERT fixture-only feasibility testing is separate from research model fitting and evaluation.
