# Dataset Source Details

This audit was completed on 2026-07-31 from the uploaded `research.zip` and fresh clones of the linked repositories. Counts below are data rows, excluding headers. A banking candidate means at least one exact keyword/phrase from `banking_filtering_plan.md` matched; it is not a final banking label.

## Uploaded AI-generated email CSV

- Paths: `research/datasets/AI_Generated_Phishing_Legitimate_Emails.csv` and `research/datasets/ai_generated_datasets/AI_Generated_Phishing_Legitimate_Emails.csv` inside the uploaded ZIP.
- Integrity: both files are byte-identical (`SHA-256 110d8758408ee748502d3c3ea36519caefa21c68f6bc69322716c0f26d444b98`).
- Shape: 126 rows; `Subject`, `Body`, `Label`.
- Labels: 63 `Phishing`, 63 `Legitimate`.
- Channel/authorship: email; the accompanying Opara et al. paper states all 63 phishing and all 63 legitimate emails were generated with GPT-4o.
- Banking filter: 101 candidate rows.
- Decision: documented only. The article is available under CC BY-NC, but that does not by itself establish redistribution terms for this exact CSV. No duplicate is added to the unified file.

## Uploaded bank-transaction SMS workbook

Source path: `research/datasets/archive.zip/Prepared bank transactions SMS dataset .xlsx`.

| Worksheet | Nonblank data rows | Banking candidates |
|---|---:|---:|
| `debit535 1896` | 1,894 | 1,875 |
| `credit121 1386` | 1,387 | 1,387 |
| `debit2468  474` | 474 | 474 |
| `debit296  358` | 358 | 357 |
| `debit6111 230` | 230 | 100 |
| `credit510 140` | 139 | 139 |
| `credit944 22` | 21 | 21 |
| **Total** | **4,503** | **4,353** |

All sheets use `ID`, `Cardholders`, `Label`, an unnamed direction column, `Date`, and `SMS`. The `Label` column is blank throughout. The content looks like masked transactional banking alerts, but appearance is not label evidence: rows remain `unknown`, not legitimate. Authorship and license are also unknown. Used-range counts can appear higher because several worksheets contain formatted blank rows. No workbook rows are committed.

## Cross-model phishing package

Uploaded path: `research/literature/previous works ready/20250116/cross-model-phishing.zip`. Its included license states MIT for code and CC BY 4.0 for data.

### Human corpus

- File: `data/human_corpus_sampled.csv`.
- Shape: 5,000 rows; `text`, `subject`, `body`, `label`, `source`.
- Labels: all `1`, defined by the included README as phishing.
- Authorship/channel: human-written email.
- Sources: TREC-07 (1,500), CEAS-08 (1,500), Nazario (1,000), Nigerian Fraud (750), and fraud-labeled Enron (250).
- Banking filter: 1,914 candidates.
- Decision: standardized rows committed with attribution and original source in `notes`.

### LLM corpus

- File: `data/llm_corpus_sampled.csv`.
- Shape: 4,986 rows; `text`, `subject`, `body`, `label`, `source`, `model`, `category`.
- Labels: all `1`/phishing.
- Authorship/channel: AI-generated email, not a rewrite of a linked human row.
- Models: GPT-4.1 (1,665), DeepSeek 3.2 (1,665), Llama 3.3 70B (1,656).
- Generation categories: parcel delivery (999), banking (998), tax/IRS (998), HR (996), IT support (995).
- Banking keyword filter: 4,285 candidates. This is deliberately broader than the 998 generation-category rows because generic financial/security terms can appear in other categories.
- Decision: standardized rows committed.

### Feature and result files

`corpus_features.csv` has 9,986 rows and repeats the same human and LLM messages with 17 stylometric features; it is not merged again. The nested package and `results.zip` contain metric tables plus 9 duplicate examples, 8 false-negative excerpts, and 11 false-positive excerpts. These are experiment outputs or duplicate excerpts, not additional source messages.

## SmishX

- Repository/version: `yizhu-joy/SmishX`, commit `116a8c827741e0572563f678d25ed04306b1e3ff`.
- File: `data/dataset.csv`.
- Shape: 1,200 rows; `SMS`, `label`, `if_URL`, `if_phone`, `if_email`.
- Labels: 259 smishing, 319 spam, 622 legitimate.
- Channel/authorship: SMS; source does not label human versus AI, so all authorship fields are `unknown`.
- Banking filter: 173 candidates.
- Access: the repository has an MIT license and requires citation of the SOUPS 2025 paper.
- Decision: standardized rows committed. Original label and URL indicator remain in `notes`.

## SmishTank

The 2024 paper reports a 1,090-sample community-sourced snapshot with sender, message body, referenced brand, and URL/domain analysis. The current site is a JavaScript application and asks users to cite the paper, but this audit did not find a stable downloadable export with explicit redistribution terms. No site rows were scraped or committed. The site and paper remain collection references.

## PhishFuzzer

- Repository/version: `DataPhish/PhishFuzzer`, commit `1e21dd4edbe5c64694f156bf5318c97c7c80681c`.
- `PhishFuzzer_emails_original_seed_v1.json`: 3,300 rows (1,126 phishing, 1,074 spam, 1,100 valid); 1,895 banking candidates. The `Created by` field is mostly `Human` but contains inconsistencies.
- `PhishFuzzer_emails_entity_rephrased_v1.json`: 19,800 LLM rows (6,756 phishing, 6,444 spam, 6,600 valid); 15,261 banking candidates. Six variants per original are linked by `Original_ID` and vary entity type and length.
- `emails_expanded_2026_Gemini.json`: 23,100 rows, representing the combined seed/expanded collection; it should not be combined again with the two top-level release files.
- Decision: documented only. No `LICENSE` file or explicit dataset license was found in the repository as cloned. These would be the most relevant AI-rewritten rows after permission or license clarification.

## PhishOracle repositories

The project repository (`9e4e475ecfc77edce3b35e9bfc2fdd6fb2d2291c`) and web app (`490940274cf3d3a5bf86f0c643873ab9db491d31`) contain webpage-generation code and HTML assets, not text-message datasets. Neither clone contained a license file. They are excluded from the unified text-message CSV.

## Committed processed totals

| File | Rows |
|---|---:|
| `unified_text_messages.csv` | 11,186 |
| `banking_candidates.csv` | 6,372 |
| `banking_manual_review.csv` | 6,372 |
| `banking_human_written.csv` | 1,914 |
| `banking_ai_generated.csv` | 4,285 |
| `banking_ai_rewritten.csv` | 0 |

The candidate total includes 173 SmishX rows whose authorship is unknown. Therefore, the human and AI-generated files do not sum to all candidates. The AI-rewritten file intentionally contains only its header because the available rewrite dataset lacks clarified redistribution terms.
