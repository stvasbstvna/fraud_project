# Reproduction and artifact locations

Use **corrected_run** results. Root-level v3 model/detection/figure outputs describe a preserved invalidated run. Historical v1/v2/v2.1/v2.2 files remain unchanged.

## Existing evidence: read-only checks

```powershell
.\.venv\Scripts\python.exe -m src.benchmark_v3.verify
.\.venv\Scripts\python.exe -m pytest -q --basetemp .pytest_cache/v3-reproduction-check
.\.venv-benchmark-v3\Scripts\python.exe -m pytest tests/benchmark_v3/test_modernbert.py -q --basetemp .pytest_cache/v3-modernbert-reproduction-check
```

The verifier reads the immutable source/review/model evidence and writes an identical verification receipt only. It does not call an API, fit models or modify historical files.

## Pipeline replay with existing snapshots/caches

```powershell
.\.venv\Scripts\python.exe -m src.benchmark_v3.ingest
.\.venv\Scripts\python.exe -m src.benchmark_v3.semantic_review --stage controls --version v3.1 --offline
.\.venv\Scripts\python.exe -m src.benchmark_v3.semantic_review --stage positives --version v3.1 --offline
.\.venv\Scripts\python.exe -m src.benchmark_v3.correction lexical
.\.venv-benchmark-v3\Scripts\python.exe -m src.benchmark_v3.correction modern_train
.\.venv-benchmark-v3\Scripts\python.exe -m src.benchmark_v3.correction modern_infer
.\.venv\Scripts\python.exe -m src.benchmark_v3.correction evaluate
.\.venv-benchmark-v3\Scripts\python.exe -m src.benchmark_v3.correction C_infer
.\.venv\Scripts\python.exe -m src.benchmark_v3.correction C_evaluate
.\.venv\Scripts\python.exe -m src.benchmark_v3.correction statistics
.\.venv\Scripts\python.exe -m src.benchmark_v3.correction reports
```

Existing frozen model manifests are verified and reused rather than retrained; changed settings/inputs fail. Raw requests/results remain cached. Ingest checks the pinned Git source bytes (allowing recorded Git CRLF checkout conversion), not current remote main. Reports regenerate derivative plots only. Do not call `robustness.run()` against occupied output paths: that acquisition/generation stage uses exclusive files and would fail; its actual calls and frozen texts are already retained. It never needs to be rerun to replay scoring.

Fresh acquisition/training requires a clean isolated copy with new output paths, the pinned repository/revision, rights evidence, separate model environment and reviewed source plan. Do not replace the frozen source cohort or overwrite this run to add sources. The initial clone downloaded Git objects and required SMS files; unrelated email LFS fetching was interrupted. Required source files were verified against the exact Git objects. No malicious message URL was opened.

## Files

* `data/benchmark_v3/provenance/`: repository/file manifest, rights registry, Sting9 page/Swagger/HTTP snapshots.
* `data/benchmark_v3/candidates/`: permitted defanged candidates; generic spam/ham remain unvalidated until review.
* `data/benchmark_v3/review/`: both instrument versions, source-only policy checks and actual role-bound raw requests/responses. No API keys or authorization headers are serialized.
* `data/benchmark_v3/corrected_run/frozen/`: authoritative modeling/source-holdout cohorts and manifest.
* `data/benchmark_v3/robustness/`: unchanged blind generation attempts/reviews and original stimulus freeze.
* `data/benchmark_v3/corrected_run/robustness/`: exact corrected-heldout stimulus intersection; no regenerated text.
* `models/benchmark_v3/modernbert_base_source/`: official pinned base model/tokenizer; `modernbert_source_manifest.json` records hashes.
* `models/benchmark_v3/corrected_run/`: frozen LR/RF and fine-tuned ModernBERT for both experiments; separate environment freeze and fit audit.
* `results/benchmark_v3/corrected_run/`: authoritative A/B/C predictions, metrics, source strata, paired statistics, sixteen tables, ten PNG/SVG figures and verification.

The existing `.venv` remains unchanged. ModernBERT dependencies reside in `.venv-benchmark-v3`; original and corrected package inventories are recorded separately. Exact source checkpoint is `answerdotai/ModernBERT-base` revision `8949b909ec900327062f0ebf497f51aef5e6f0c8`. CPU is the actual training device, not a silent model substitution.
