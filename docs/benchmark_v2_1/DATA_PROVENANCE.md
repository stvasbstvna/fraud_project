# Data provenance and source decisions

Access/review date: 2026-11-06. `configs/benchmark_v2_1/source_registry.csv` contains 12 source/category entries. No external rows were downloaded, imported, relabeled or accepted for generation by this run. Metadata inspection is not a completed row-level source audit.

## Collection versus source

[SMISH_DT](https://github.com/MarazMia/SMISH_DT) is an aggregator with original/refined datasets, emails, phone/URL lists and notebooks. Its README links original sources; no root license covering all included rows was visible. Refined URL-analysis fields do not establish message ground truth, and extracted URL lists lose direct message indexes. Do not combine raw and refined copies or extracted URLs as independent messages.

## Priority sources

- **Mendeley:** [original v1 record](https://data.mendeley.com/datasets/f45bkkt8pr/1), DOI 10.17632/f45bkkt8pr.1, Mishra/Soni, 2022. Original documentation reports three classes and OCR-based collection; LABEL/TEXT/URL/EMAIL/PHONE are documented. CC BY 4.0 is explicitly shown. Candidate for attributed use, not yet accepted: examine original rows, language, bank relevance, annotation definitions/ambiguity and overlap with frozen training data first. Documentation identifies categories but does not supply a sufficiently detailed annotation rubric for automatically treating every row as definitive phishing ground truth. Never merge spam into phishing.
- **SmishTank:** [original paper](https://arxiv.org/abs/2402.18430). The local UTF-8 snapshot has 1,062 rows and separate message, brand and URL-analysis fields. `Detected`, `Malicious`, `Phishing`, `Suspicious`, `Malware` may describe URL evidence. Hold new confirmatory inclusion until message-level review and redistribution terms are verified. The site export was inaccessible through the browser tool. Existing local training data already includes this source; normalization/template matching against train/validation is mandatory.
- **SMS Gateway:** [original repository](https://github.com/wspr-ncsu/sms-phishing) shows an MIT license and describes message inclusion via VirusTotal/APWG. Potential phishing candidates, not human-confirmed banking ground truth or a source of legitimate controls. Verify license scope, English/banking subset and campaign clustering before inclusion.
- **SpamHunter:** [original repository](https://github.com/opmusic/SpamHunter_dataset) documents categorized spam; no license visible in the root listing. Hold. Spam categories and URL extraction do not justify universal phishing labels.
- **Super SMS:** [original repository](https://github.com/smspamresearch/spstudy) cites the 2024 IEEE Access paper. License, exact class semantics and constituent overlap remain unresolved. Hold.
- **SmishX:** [original repository](https://github.com/yizhu-joy/SmishX) describes manual re-labeling into smishing/spam/legitimate and has MIT licensing. Existing project provenance pins commit `116a8c827741e0572563f678d25ed04306b1e3ff`. Because the frozen detector training set includes SmishX, exclude all train/validation exact/template overlaps. Upstream row rights require separate attention. External-validation candidate only at present.

## Other source categories

[UCI SMS Spam Collection](https://archive.ics.uci.edu/dataset/228/sms+spam+collection) explicitly shows CC BY 4.0 and describes its mixture of NUS and other source collections. English banking ham may become reviewed controls; UCI spam is not a phishing label. [ExAIS](https://github.com/AbayomiAlli/SMS-Spam-Dataset) is identified, but detailed licensing, labels and row-level review are still pending. NUS and multilingual collections require original-source checks; no blanket permission is inferred. Non-English and email data are excluded from the English SMS primary population.

## Current canonical candidates

`source/frames.csv` derives only from existing safe project-authored synthetic anchors, with original legacy row IDs retained. 441 unique normalized texts: 254 phishing-labelled candidates, 187 legitimate-labelled candidates. These are **candidate labels**, not validated true labels. 809 repeated legacy rows appear in `results/benchmark_v2_1/diagnostics/exact_duplicates.csv`; 22,406 within-entity near-duplicate pairs (SequenceMatcher ≥0.90) remain diagnostics. Exact deduplication does not remove template-family dependence.

No new source is accepted for confirmatory evaluation. No external source is declared permanently unusable merely because rights are unresolved. Non-English/email sources are rejected for the primary population because they change controlled language/channel. Synthetic candidates are held for semantic/action/intent review rather than presented as validated phishing messages.

## Proposed labeling policy

Retain original dataset and source-row identifiers and original labels. Map only reviewed smishing/phishing evidence to `phishing_scam`; ham to `legitimate` only with source evidence and context review. Generic spam, ambiguous security notices, unverifiable context and URL-only verdicts are excluded or adjudicated, never forced into binary ground truth. Preserve label disagreement evidence. Banking relevance must be explicitly reviewed; keyword hits are candidate selection only. Any source accepted later needs pinned revision/checksum, license evidence, attribution, privacy/defanging review, training/template overlap diagnostics, human label evidence and a prospective selection rule before generation.
