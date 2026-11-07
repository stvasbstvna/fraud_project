# Source audit scope and provenance — v2.2

This is a deterministic feasibility audit, not semantic approval or human annotation. The 81,738 inspected message rows include repeated and historical sources; they are not 81,738 independent messages. The broad keyword/known-institution screen retained 23,731 candidates. It can miss banking context expressed without recognized terms; no claim is made about all possible banking messages or all available datasets worldwide.

## Actually read message inputs

| Source | Input rows | Version / rights evidence | Use |
|---|---:|---|---|
| Mishra/Soni Mendeley SMS | 5,971 | v1, CC BY 4.0, original archive SHA verified | Broad candidates, fresh typed redaction |
| UCI SMS Spam Collection | 5,574 | Original archive, CC BY 4.0 on publisher page, archive SHA verified | Ham candidates only; spam never promoted to phishing |
| SMS-Gateway | 68,029 | Pinned `a4f18cedc9909cbf8234eea3c2028080a1e95cd4`, MIT repository evidence retained in historical source notice | Phishing candidates only; malformed header parsed by verified ordinal fields |
| Ahmed/Islam financial scams | 523 | Mendeley v2, CC BY 4.0; publisher metadata and CSV SHA verified | Newly expanded source; HOLD for row-level channel |
| SmishX local normalized copy | 1,200 | Recorded original commit `116a8c827741e0572563f678d25ed04306b1e3ff`, repository MIT, upstream scope unresolved | Audited; HOLD; existing training overlap |
| Historical synthetic anchors | 441 | Project-authored v2.1 candidates, not new data | Historical reference; all 187 legitimate candidates overlap prior benchmark |

Mishra and Soni (2022), DOI [10.17632/f45bkkt8pr.1](https://data.mendeley.com/datasets/f45bkkt8pr/1); Almeida and Hidalgo (2011), DOI [10.24432/C5CC84](https://archive.ics.uci.edu/dataset/228/sms+spam+collection); Nahapetyan et al., [SMS phishing repository](https://github.com/wspr-ncsu/sms-phishing); Ahmed and Islam (2025), DOI [10.17632/znsk27yk3h.2](https://data.mendeley.com/datasets/znsk27yk3h/2); Wang et al., [SmishX SOUPS 2025](https://github.com/yizhu-joy/SmishX). Source modifications: typed safety redaction, candidate filtering, family/overlap screening and lineage flags. [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/) requires attribution; no endorsement is implied. Gateway's retained MIT notice is `data/benchmark_v2_1/source/pilot_gateway_LICENSE.txt` (unchanged).

The new financial collection has 310 scam and 213 ham rows. Publisher documentation says it mixes English/Bangla and SMS/chat/email; CSV fields are only `label,message`. Of 213 broad financial candidates, 64 are ham and 149 scam. No per-row channel exists. SMS-like style cannot establish SMS provenance, so these rows remain on HOLD. Its file SHA is `58ec802e4de8768643e3be0badbaedb3ae5017a273e8f3898e72f6a29cbc96ad`. A scam label would still require banking/phishing review if channel were resolved.

The candidate field `real_vs_synthetic=real` is an optimistic classification of public nonsynthetic-source candidates, not verified human authorship or real bank authenticity. No final real legitimate controls were approved. Source metadata cannot establish bank origin from a ham label.

## Other local and discovered resources

* The same local unified file contains 9,986 cross-model email rows. They were inventoried and excluded by channel, not relabeled SMS.
* The historical inventory documents a 4,503-row bank-transaction workbook with blank labels and unclear source/license. No such original workbook was present in the current workspace file inventory. Historical descriptions were inspected; 4,503 new messages were not read or imported. Authenticity, consent and exact dataset rights remain unresolved.
* Local controls, final test files, review exports, historical benchmark variants and ZIP update packages are derived evidence, not independent new source groups. Training/validation and prior benchmark texts are screening references only; detector probability columns were not loaded for source decisions.
* [SpamHunter](https://github.com/opmusic/SpamHunter_dataset) provides categorized spam, not an established legitimate banking control source; no explicit dataset license was found in the checked repository listing. [Super SMS](https://github.com/smspamresearch/spstudy) requests citation but did not supply clear dataset licensing in the checked listing. No rows were silently imported.
* [NUS SMS corpus repository](https://github.com/kite1988/nus-sms-corpus) has English/Chinese archives and no license in the checked root listing. No new row audit or rights clearance was completed; NUS/UCI lineage overlap also needs checking.
* [FinEE](https://huggingface.co/datasets/Ranjit0034/finee-dataset/blob/main/README.md) is tagged synthetic and mixes SMS/email/transaction notifications. [Indian payment SMS corpus](https://github.com/skyaara/indian-payment-sms-dataset) explicitly describes authored synthetic messages. Neither solves the real-control requirement; neither was used to fill the cohort.
* SmishTank and PhishFuzzer retain prior rights/provenance or channel limitations. A license for a paper or code is not silently extended to all embedded messages. No private inbox or personal banking account was accessed.

## Independent-source bound

Control-only template screening used the unchanged numerical v2.1 pair thresholds: Jaccard >=0.80 and structural similarity >=0.80, or structural similarity >=0.92 and Jaccard >=0.45. Institution/placeholder normalization and connected components apply to candidates and references consistently. Dates are not corrupted into phones. Train/validation and prior benchmark witnesses propagate through a family.

There are 100 rule-clear ham candidate rows, 50 from each of Mendeley-SMISH and UCI, spanning 49 families. **43 of the 50 Mendeley rows have exactly the same original-text SHA-256 as UCI rows**. Those rows receive UCI-LINEAGE rather than independent Mendeley provenance. The remaining seven Mendeley families are optimistically treated as independent; no unsupported claim is made that they really are independent bank controls. Lineage family capacities are UCI 48 and Mendeley 7. Family overlap between groups is deliberately double-counted in the capacity calculation to make it an upper bound.

With at most half a class from a single lineage, at most seven UCI-lineage controls can accompany seven non-UCI candidates: **maximum 14**, before semantic rejection and before enforcing unique families across both selected groups. All 187 synthetic controls are prior-overlapping, so none can rescue capacity under the <=25% synthetic rule. This proves the screened pool cannot meet the 16-control gate; it does not prove no further suitable dataset exists.

Complete positive-family clustering and semantic review were not needed to establish this control shortage and are explicitly NOT RUN. The 23,005 positive candidate capacity bound counts unscreened rows optimistically and is not a count of approved phishing families. No source cohort was frozen and no generation followed.

Exact row-level evidence: `data/benchmark_v2_2/source/candidate_audit.csv`, `source_registry.json`, `reference_manifest.json`; summarized in `results/benchmark_v2_2/source_audit_counts.csv` and `tables/Audit_control_lineage.csv`. Original licensed snapshots were stored separately in v2.2; none of the source-message endpoints was visited.
