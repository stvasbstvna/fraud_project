# Dataset Collection Plan

## Current decision

Actual standardized rows are committed only from sources whose available materials support redistribution: SmishX under its repository MIT license and the uploaded cross-model package under its included CC BY 4.0 data license. Other sources are fully inventoried but not copied into the repository.

## Source decision table

| Source | Available locally | Redistribution decision | Next action |
|---|---|---|---|
| SmishX | yes, cloned at recorded commit | include standardized rows | preserve citation and commit hash |
| Cross-model human/LLM package | yes, uploaded ZIP | include standardized rows | preserve CC BY attribution and source notes |
| Uploaded GPT-4o email CSV | yes, two identical copies | document only | locate exact Kaggle record and dataset license |
| Uploaded bank-transaction XLSX | yes, nested ZIP | document only | identify creator, collection method, consent/privacy basis, and license |
| PhishFuzzer | yes, cloned at recorded commit | document only | request or locate explicit code/data license and verify upstream terms |
| SmishTank | site and paper available | document only | obtain a stable versioned export and written terms |
| PhishOracle repositories | code available | exclude from text-message corpus | use only as a robustness-method reference |

## Reproduction

After obtaining the three license-cleared input CSVs locally, run:

```bash
python -m src.build_dataset_files \
  --smishx /path/to/SmishX/data/dataset.csv \
  --cross-model-human /path/to/human_corpus_sampled.csv \
  --cross-model-llm /path/to/llm_corpus_sampled.csv \
  --output-dir data/processed
```

The builder does not download data, access message URLs, or infer authorship beyond source documentation. It keeps every source row, adds stable IDs, maps source labels, defangs URLs, applies the published banking filter, and produces the six requested files.

## Collection procedure for new sources

1. Save the source URL, repository commit or version, retrieval date, file SHA-256, citation, and exact license text.
2. Confirm that the license covers message data, not only the paper or code.
3. Record row count, columns, text and label fields, label distribution, channel, and authorship evidence.
4. Store unmodified files outside Git under `data/raw/<source_id>/`.
5. Scan for direct identifiers and live URLs. Define redaction and defanging before producing a processed copy.
6. Map values to `dataset_schema.md`; use `unknown` where evidence is absent.
7. Apply the keyword filter. Do not convert a candidate flag into a final banking label.
8. Add candidates to manual review and retain reviewer decisions separately from source labels.
9. De-duplicate only after preserving source IDs and rewrite-family links. Report how many rows were removed.
10. Freeze split groups so an original message, duplicates, and all rewrites remain in one split.

## Planned PhishFuzzer integration

If licensing is clarified, use the 3,300 seed rows and 19,800 entity-rephrased rows rather than also importing the 23,100-row combined intermediate file. Map `Original_ID` to a future pair/family field, set source-supported LLM variants to `is_ai_rewritten=true`, retain `Type` as the message class, and preserve `Motivation`, `Entity_Type`, and `Length_Type` in an extended provenance table. Do not silently change the required 17-column export.

## Planned SmishTank integration

Use an official, versioned export rather than scraping the interactive table. Preserve message ID, sender, body, brand, and defanged URL/domain metadata. Because the paper corpus contains phishing reports rather than legitimate controls, do not infer a negative class.

## Quality gates

- Every processed row has a unique nonblank ID and text.
- All labels/channels/authorship flags are within documented values.
- Candidate rows have at least one recorded banking keyword; non-candidates have none.
- AI-rewritten rows have a source-supported rewrite relationship.
- Output counts reconcile to source counts and are recorded in `dataset_source_details.md`.
- No committed URL begins with `http://` or `https://`.
- Header-only files remain header-only when no license-cleared rows fit the category.
