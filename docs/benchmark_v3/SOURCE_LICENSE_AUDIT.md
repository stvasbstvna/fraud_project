# Benchmark v3 source rights and provenance audit

Audit date: 2026-11-06 (session date). These decisions concern the original sources, not a license inferred from SMISH_DT. Public access alone does not establish permission. Modeling eligibility below is separate from label eligibility and raw redistribution. Source record/file hashes and exact aggregator commit belong in the acquisition manifest.

| Source | Original evidence | Local modeling | Raw redistribution | Label/population limitation |
|---|---|---|---|---|
| Mendeley Smishing v1 | [Dataset DOI 10.17632/f45bkkt8pr.1](https://data.mendeley.com/datasets/f45bkkt8pr/1), Licence section: CC BY 4.0 | Allowed with attribution | Allowed with attribution, license link and change notice | LABEL is ham/spam/Smishing; only explicit Smishing is phishing candidate; ham needs financial and semantic review. Source acknowledges Almeida and Sonowal: check cross-source duplicates. |
| UCI SMS Spam Collection | [Official UCI #228](https://archive.ics.uci.edu/dataset/228/sms+spam+collection), License: CC BY 4.0 | Allowed with attribution | Allowed with attribution and change notice | spam is unsolicited content, not universally phishing. ham is largely student/personal dialogue, not banking notification ground truth. Contains earlier NUS ham; not independent of NUS. |
| NUS/Singapore SMS Corpus | [Authors' paper](https://arxiv.org/html/1112.2468), sections 4.4 and 6; [author release README](https://github.com/kite1988/nus-sms-corpus) | Allowed under authors' public-domain statement; cite Chen and Kan | Allowed under authors' copyright-free unlimited-use statement; cite and retain provenance | No row-level spam/phishing/legitimacy annotation. Real contributed SMS, not guaranteed legitimate bank messages. Filter language and assess financial function and suspicious content. |
| SMS Gateways / sp24 | [Original data-release README](https://github.com/wspr-ncsu/sms-phishing), [MIT LICENSE](https://github.com/wspr-ncsu/sms-phishing/blob/main/LICENSE) | Allowed under repository MIT release | Allowed retaining copyright and MIT permission notice | Explicit phishing corpus: gateway messages flagged by VirusTotal/APWG. No legitimate controls. Malware/URL verdict is supporting evidence, not independently audited message intent. |
| ExAIS | [Original author README](https://github.com/AbayomiAlli/SMS-Spam-Dataset) | HOLD: explicit reuse grant not found | HOLD | Consent and stated spam-research purpose support real origin but do not specify downstream license. Promising banking ham, yet not cleared for this benchmark. spam does not mean phishing. |
| Super SMS | [Original author README](https://github.com/smspamresearch/spstudy) | HOLD: no explicit license found | HOLD | Citation request alone is not reuse license. Merged sources and augmented messages require component provenance and origin review; ham cannot automatically be bank control. |
| SpamHunter | [Original dataset README](https://github.com/opmusic/SpamHunter_dataset) | HOLD: no explicit license found | HOLD | Twitter screenshot OCR; spam corpus and category training subset, not legitimate controls. Numeric content already removed, reducing financial detail. Do not confuse unrelated spamhunter.org terms with this source. |
| SmishTank | [Dataset access URL](https://smishtank.com/dataset), [authors' paper](https://arxiv.org/abs/2402.18430) | HOLD: license not retrieved | HOLD | Publicly described human-reported smishing collection; browser extraction returned only JS application/unavailable dataset page. Open-access paper does not itself license dataset rows. |

NUS is resolved from primary authors, rather than left unknown because GitHub lacks LICENSE. Their conclusion states: **“copyright-free for unlimited use”**. Section 4.4 describes an open-license/public-domain process approved by university intellectual-property staff. This is a custom public-domain declaration, not verified CC0 legalcode. The author release specifically links the March 9, 2015 English release (55,835 messages). The older 2004 NUS subset and live 2010 onward corpus may differ in governing notice; preserve release identity and inspect embedded notices if distributing old-only material.

Mendeley author metadata describes 5,971 messages: 4,844 ham, 489 spam and 638 smishing; it explicitly describes use as labeled deep-learning data. Those are publisher-reported counts, not this pipeline's parsed totals. Its screenshots/OCR collection method and acknowledgement of previous corpora limit independence and originality claims. UCI's web total is 5,574; actual downloaded row count must prevail when implementation differs. Do not inflate sample size using publisher totals.

The Gateway repository expressly calls itself a data release and carries a repository MIT license with no separate data exclusion found. MIT's boilerplate uses software terminology; record repository-level scope, rather than inventing a Creative Commons data license. Include original 2023 wspr-ncsu copyright and permission notice in substantial redistributed extracts.

## Inspected aggregator schemas

- `Mendeley_Dataset_5971.csv`: `LABEL,TEXT,URL,EMAIL,PHONE`.
- `UCI_SMSSpamCollection`: tab-separated original label and message, no header.
- `Singapore_smsCorpus_en_2015.03.09_all.json`: `smsCorpus.message[]`; row `@id`; `text.$`; `messageProfile.@language`, `.@time`, `.@type`; contributor metadata and `collectionMethod.@time`. Collection time must not be substituted for unknown message time.
- `super_sms_dataset.csv`: `SMSes,Labels`.
- `SPAM-Hunter_full_dataset_messages.csv`: `Messages` only; source-wide spam provenance, no per-row phishing label or legitimate label.
- `smishtank.csv`: messageid, Fulltext, Sender, SenderType, timeReceived, MainText, URL and threat/brand metadata. URL detection fields are not independent message ground truth.
- Gateway `phishing_messages.csv`: messageID, objectID, destination number, message, X, time, error in time; campaigns file has campaignID, objectID, number of messages, start/stop timestamps, message and urls. Treat error-in-time and units explicitly before temporal use.
- ExAIS distribution includes per-user CSVs plus merged/cleaned files. Do not concatenate these together: they represent overlapping views.

## Recommended admissible groups

Proceed with Mendeley, UCI, NUS, and Gateway under their recorded terms. Candidate legitimate financial controls can come from semantically reviewed Mendeley ham, UCI ham, and NUS contributed SMS. NUS financial personal transfers can be meaningful financial controls under the user's broad population, but must be reported separately from institution-origin transaction/security alerts. NUS has no automatic ham label: provenance plus semantic review must support each retained control. ExAIS appears especially promising for real banking notifications, but remains outside modeling until a concrete reuse grant is obtained. No author messages were sent.

Keep source-specific adjudication: financial advertising, promotional loans, prize spam, generic OTP and personal discussions about money require function/intention review. Neither a bank keyword nor an existing ham/spam label establishes the target class. Licensed controls may still be too scarce for 300 independently templated legitimate bank messages; report observed scarcity rather than synthesizing replacements.

This audit records retrieved primary evidence and project eligibility decisions, not a guarantee that a dataset depositor owns every third-party message. The SMISH_DT README is a provenance pointer only. Refined datasets, URL-analysis directories and aggregator labels cannot expand original reuse rights or fix source annotation limitations.
