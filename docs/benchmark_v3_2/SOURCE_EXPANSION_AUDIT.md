# Benchmark v3.2 source expansion audit

Audit date: 2026-11-07. Additive discovery only. No v3 files, frozen cohorts, detectors, scores or existing reports were changed. This is a source candidate expansion, not an expanded legitimate cohort. No API review was performed by this source-discovery task.

`data/benchmark_v3_2/source/new_source_candidates.csv` contains novel lexical candidates from already rights-cleared real SMS sources. Every candidate and validated label is `uncertain`. Source reuse permission is distinct from English, financial-service function, sender authenticity and legitimate class eligibility. Most inspected new NUS matches are personal money conversations and should be excluded under the financial-service population rule.

## Rights and provenance

- **NUS March 9, 2015 English release**: primary [author release](https://github.com/kite1988/nus-sms-corpus) identifies the release and asks citation to Tao Chen and Min-Yen Kan (2013), *Creating a Live, Public Short Message Service Corpus*. The [author paper](https://arxiv.org/html/1112.2468), sections 4.4 and 6, describes the public-domain process and calls the corpus copyright-free for unlimited use. This custom author declaration is the rights basis, not a fabricated CC0 label. The corpus includes contributed historical SMS, not bank-verified notifications or universal ham labels. `raw_label=unlabeled` is preserved.
- **Mendeley Smishing v1**: [original publisher record](https://data.mendeley.com/datasets/f45bkkt8pr/1), CC BY 4.0, as documented in existing v3 primary rights evidence. Ham only was eligible for this expansion; ham remains merely source evidence. Retain publisher attribution, license link and change notice.
- **UCI SMS Spam Collection**: [official source](https://archive.ics.uci.edu/dataset/228/sms+spam+collection), CC BY 4.0; attribute Almeida and Hidalgo and retain provenance. Ham only was eligible. Some UCI and Mendeley rows derive from NUS and cannot establish independent source diversity.

Only minimized text is exported; URLs, emails and long numeric strings are replaced with typed placeholders. Raw source files stay unchanged. Amounts and language remain where the generic numeric redactor does not match. Original-text and source-file SHA256 hashes make selection auditable. This independent redactor may differ from v3 redaction; subsequent global normalization and family filtering remain necessary.

## Exhaustive local expansion algorithm

The executable PowerShell acquisition/selection record is `data/benchmark_v3_2/source/acquisition_evidence/expand_local_sources.ps1`. It scans all 55,835 NUS, 5,971 Mendeley and 5,574 UCI rows. It selects a deliberately broad expanded vocabulary including pay/paid, withdrawals, remittances, funds, cheques, money, salary, invoices, bills, ATM and Singapore bank abbreviations, plus currency symbols. It excludes all old v3 candidate representative and origin IDs, all reviewed IDs, explicit spam/smishing/phishing source labels, normalized exact old candidate safe text and exact new duplicates. No stochastic sample or detector scores are used. Mendeley and UCI row IDs use the same one-based physical-record convention as existing v3 readers; NUS uses native @id. JSON/TSV decoding is explicitly UTF-8.

The export contains **707** unique lexical candidates: **658 NUS**, **40 Mendeley ham** and **9 UCI ham**. The resulting counts and exact source hashes are in `local_expansion_manifest.json`. Financial evidence is the literal matched vocabulary; it is **not** semantic financial eligibility. No training compatibility prefilter was applied. Very short bank fragments and incidental uses such as ATM meaning “at the moment” are retained for transparent subsequent semantic exclusion. One promising source-level find is `nus-7679`, a SIB password/PIN safety warning. It is still uncertain pending the independent review; no sender authenticity was invented.

## Additional discovery and exclusions

| Source or pool | Primary evidence inspected | Decision |
|---|---|---|
| MOZ-Smishing | [Original author dataset card](https://huggingface.co/datasets/MOZNLP/MOZ-Smishing/raw/main/README.md) declares language pt and CreativeML OpenRAIL-M, with 552 smishing and 2,009 legitimate messages | Portuguese population; no translation or English-control fabrication. Financial M-Pesa notifications in the visible preview were Portuguese. |
| Revised Indian | [Release repository](https://github.com/shshnk158/Multilingual-SMS-spam-detection-using-RNN) linked by SMISH_DT, a fork of manohar9600 | No explicit reuse grant established in inspected release; held out, no downstream license inferred from aggregator. |
| ExAIS / Super SMS / British English | Existing local raw pools, SMISH_DT provenance, existing `docs/benchmark_v3/SOURCE_LICENSE_AUDIT.md` and [British release](https://mtaufiqnzz.wordpress.com/british-english-sms-corpora/) | No newly established original reuse grant. No candidates exported under a guessed license. |
| Indian payment SMS | [Author release](https://github.com/skyaara/indian-payment-sms-dataset) explicitly describes a privacy-safe synthetic corpus | Synthetic; excluded from real source controls even though openly licensed. |
| Gateway / SpamHunter / SmishTank / Sting9 | Existing primary audits and raw source descriptions | Phishing/spam/report collections, not a source of verified legitimate controls; no ham invented. |
| Korean/Bangla/Bengali sources | Local SMISH_DT source identities | Wrong language; no translated substitutes. |
| Enron | Local email corpus | Email is outside SMS channel. |

Primary source pages were fetched through web browsing. Direct shell HTTP snapshot attempts were network-blocked; failed attempts are preserved in `retrieval_manifest.json` and must not be mistaken for successful acquisitions. The exact primary-page observations are preserved in `primary_web_evidence.json`; those records distinguish retrieved statements from search discovery.

No new independent institution-origin bank notification collection with demonstrated real origin, English population and original reuse rights was established. The largest admissible local expansion is the exhaustive lexical candidate CSV. Counts must not be described as additional legitimate controls until semantic review and global family exclusion complete. This finding reflects inspected sources, not proof that no such dataset exists.


Verification found native NUS ID 18088 attached to two distinct texts. Both ambiguous rows were removed. The export has 707 unique IDs and no prior candidate/origin ID overlap.

