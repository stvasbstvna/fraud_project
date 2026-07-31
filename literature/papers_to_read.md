# Papers and Technical Sources to Read

## Core reading

1. Gutierrez, Villegas-Ch, and Govea (2026), *Cross-model evaluation of phishing detectors against LLM-generated emails*. Most direct source on authorship detection, generator shift, threshold calibration, and pooled training.
2. Toth, Gruschka, and Bisztray (2026), *The Phish, The Spam, and The Valid*. Connects PhishFuzzer's human-seeded LLM variants, intent labels, and email metadata to robustness benchmarking.
3. Opara, Modesti, and Golightly (2025), *Evaluating spam filters and Stylometric Detection of AI-generated phishing emails*. Useful evidence on commercial-filter bypass and stylometric mitigation.
4. Kulal et al. (2025), *Robust ML-based Detection of Conventional, LLM-Generated, and Adversarial Phishing Emails Using Advanced Text Preprocessing*. Relevant to adversarial preprocessing and deployment tests.
5. Francia et al. (2024), *Assessing AI vs Human-Authored Spear Phishing SMS Attacks*. Human judgment study of AI- and human-authored SMS persuasiveness.
6. Wang et al. (SOUPS 2025), *Can You Walk Me Through It? Explainable SMS-Phishing Detection Using LLM-Based Agents*. SmishX detection/explanation pipeline and relabeled SMS dataset.
7. Timko and Rahman (2024), *Smishing Dataset I: Phishing SMS Dataset from Smishtank.com*. Dataset provenance and collection details for SmishTank.
8. Kulkarni et al. (2025), *From ML to LLM: Evaluating the Robustness of Phishing Webpage Detection Models against Adversarial Attacks*. A useful robustness-design analogy, although the object is webpages rather than messages.
9. Ahmed and Pourmoafi (2026), *Adversarial Robustness of Phishing Email Detection*. Uploaded preprint comparing TF-IDF + Logistic Regression and DistilBERT; verify publication status before relying on results.

## Context reading

- Field Effect, *2026 Cyber Threat Outlook*.
- Register.bank, *Phishing: A Cybersecurity Threat Overview for Banks*.

## Reading questions

For each work, record the message channel, source and size of data, meaning of the authorship label, whether examples are paired, split strategy, detector access, metrics, false-negative behavior, mitigation, and licensing. Results from generated-only versus human-only corpora must not be presented as paired rewrite evidence.

## Explicit exclusion

Smishing-4C is not part of this project and should not be added back to the reading or dataset plan.
