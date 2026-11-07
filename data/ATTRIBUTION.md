# Dataset Attribution and License Notes

## SmishX

Standardized rows from `SmishX/data/dataset.csv` were retrieved from commit `116a8c827741e0572563f678d25ed04306b1e3ff`. The repository includes an MIT License and identifies the dataset as manually relabeled from public sources. Cite:

Yizhu Wang, Haoyu Zhai, Chenkai Wang, Qingying Hao, Nick A. Cohen, Roopa Foulger, Jonathan A. Handler, and Gang Wang. “Can You Walk Me Through It? Explainable SMS-Phishing Detection Using LLM-Based Agents.” SOUPS 2025.

Repository: https://github.com/yizhu-joy/SmishX

## Cross-model phishing package

The uploaded package states that code is MIT licensed and data is CC BY 4.0. Standardized rows come from `human_corpus_sampled.csv` and `llm_corpus_sampled.csv`; `corpus_features.csv` is not imported again because it contains the same 9,986 messages with derived features.

Cite:

Rommel Gutierrez, William Villegas-Ch, and Jaime Govea. “Cross-model evaluation of phishing detectors against LLM-generated emails.” *Frontiers in Big Data* 9 (2026), 1883452. https://doi.org/10.3389/fdata.2026.1883452

The included README also asks users to cite the accompanying dataset record, but its placeholder Zenodo DOI was not complete in the supplied package. That unresolved identifier is retained as a provenance limitation.

## SmishTank

The local source file `data/raw/smishtank/analysisdataset.csv` contains 1,062 rows. The import script removes eight exact normalized duplicates, producing 1,054 normalized rows before cross-source deduplication. Cite:

Timko and Rahman. “Smishing Dataset I: Phishing SMS Dataset.” 2024. https://arxiv.org/abs/2402.18430

Project site: https://smishtank.com/

The paper and public project describe the dataset, but an explicit row-level redistribution license was not found in the supplied file. Therefore the raw file stays ignored by Git. Before making a public repository, verify the current SmishTank redistribution terms; if permission is not confirmed, publish the importer, checksums/metadata, and derived aggregate results rather than the raw or normalized message rows.

## Excluded row-level sources

No message rows from the uploaded GPT-4o CSV, bank-transaction workbook, PhishFuzzer, or PhishOracle repositories are redistributed here. SmishTank is used locally for the final experiment, subject to the redistribution warning above. Paper access or a public website is not treated as permission to republish dataset contents.
