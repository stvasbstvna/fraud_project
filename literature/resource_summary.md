# Resource Summary

The collected work points to a consistent problem: high in-distribution accuracy does not establish robustness to AI-assisted rewriting. Recent email studies show that older corpora can miss modern linguistic and structural patterns, while cross-model work shows that a detector can learn generator-specific cues. SmishX demonstrates how intent, brand, URL, and external context can support explanations, but its main task is SMS detection rather than paired human-to-AI evasion testing. PhishOracle shows the value of evaluating a detector on controlled adversarial variants, although it operates on webpages.

For this project, the strongest design is therefore a paired benchmark. The source message and rewrite should share an intent/action label and split group. Performance should be reported by channel and provenance, not only as one pooled score. The primary harm-relevant outcome is a false negative on a scam message, so false-negative rate and its increase under rewriting matter more than accuracy alone.

The uploaded archive contributes candidate data and methodology references, but it does not contain a completed final benchmark. In particular, the AI-generated email CSV has phishing and legitimate labels but needs provenance and license confirmation; the bank-transaction workbook appears to be useful legitimate SMS material but needs schema and license review; and the cross-model package is licensed and reproducible but compares human and independently generated phishing rather than paired rewrites.

## Organizational lessons from related repositories

- SmishX separates data, user-study materials, executable code, configuration, requirements, and a repository map.
- PhishOracle separates the generator tool from the web application and documents the experimental models and datasets.
- PhishFuzzer separates dataset creation, normalization/rephrasing, classification, raw results, and analysis.

This repository follows the same idea with distinct literature, resources, data, prompts, source code, experiments, and writing folders. It adds an explicit dataset inventory and safety policy because provenance and controlled generation are central to the question.
