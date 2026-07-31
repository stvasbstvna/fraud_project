# Project Plan

## Research logic

My earlier plan treated banking smishing as a feature-engineering problem. The newer literature suggests a more focused robustness problem: detectors may perform well on familiar corpora yet fail when an LLM changes the style without changing the scam action. I will therefore make paired human-to-AI rewrites the central experiment and treat channel and dataset as explicit factors.

## Methodology

1. Inventory sources and record access, license, channel, authorship, and label quality.
2. Convert allowed local data into one schema without committing restricted raw content.
3. De-duplicate exact and near-duplicate messages before any split.
4. Identify banking candidates using conservative rules, then manually label banking relevance and requested action.
5. Split by source-message group so a human message and all its rewrites cannot cross train/test boundaries.
6. Generate controlled rewrites only after splits are frozen. Preserve meaning and log model/version, prompt hash, parameters, date, and reviewer decision.
7. Train a TF-IDF + Logistic Regression baseline. Add Random Forest/XGBoost and DistilBERT if time and compute allow.
8. Report separate results by authorship and channel, plus paired changes for rewrite pairs.
9. Test mitigations on the same held-out pairs.

## Mitigation strategies

- Rewrite-aware augmentation using approved training-set rewrites.
- Intent/action features for requests to click, call, reply, disclose credentials, approve a transfer, or open an attachment.
- Entity and consistency checks when sender/domain metadata exists.
- Hybrid review in which uncertain or high-risk samples receive constrained LLM-assisted review.
- Validation-only threshold calibration with explicit false-negative costs.

## Limitations

- Public datasets differ in age, collection method, labels, and metadata.
- Authorship labels may be uncertain, especially for scraped messages.
- AI rewrites can introduce artifacts tied to a model or prompt.
- Banking filters can miss implicit financial scams or over-select ordinary payment language.
- Email and SMS differ in length and metadata; pooled scores may hide channel effects.
- Offline text tests do not measure live filtering or user susceptibility.

## Future work

- Replicate with unseen LLM families and multilingual messages.
- Add temporal and cross-dataset tests.
- Study URL/domain consistency and sender metadata where safely available.
- Evaluate calibrated ensembles and abstention policies.
- Seek privacy-preserving external validation with an approved partner.

## Milestones

| Phase | Deliverable | Completion rule |
|---|---|---|
| Source audit | inventory and license notes | every source has provenance and status |
| Pilot labels | banking/action annotation pilot | guidelines revised and agreement reported |
| Frozen dataset | grouped train/validation/test split | hashes and counts recorded |
| Baselines | primary model results | metrics reported by channel/authorship |
| Robustness | paired rewrite evaluation | detection gap with confidence interval |
| Mitigation | controlled comparison | same held-out set and threshold policy |
| Write-up | paper and mentor update | limitations and reproducibility checklist included |
