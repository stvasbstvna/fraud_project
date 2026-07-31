# Related Repositories and Tools

## SmishX

SmishX organizes its supplementary work into data, user-study materials, executable code, configuration, and dependencies. Its agent pipeline extracts brands and URLs, collects context, makes a decision, and generates an explanation. This project uses it as an SMS labeling and explainable-detection reference, not as evidence that paired AI rewrites have been tested.

## PhishOracle and web app

PhishOracle generates controlled adversarial webpage variants and tests detector robustness. The web app wraps that pipeline. Their separation of generation, experiment setup, and interface is a useful organizational reference. They are outside the core text-message scope and no webpage data will be mixed into the primary benchmark.

## PhishFuzzer

PhishFuzzer separates data creation, normalization, rephrasing, classification, raw results, and analysis. It offers email seeds and LLM variants with phishing/spam/valid labels, metadata, and intent fields. It is especially relevant to email schema and linguistic variation, although its variants must be checked carefully before calling them paired banking rewrites.

## Local cross-model package

The uploaded archive includes code, data, and results accompanying the 2026 Frontiers paper on cross-model phishing detection. Its code/data license states MIT and CC BY 4.0 respectively. Its grouping of pipeline steps and generator-held-out evaluation informs this repository's design. Raw package files remain outside Git pending a deliberate data decision.
