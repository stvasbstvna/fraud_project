# Final verification evidence

2026-11-07, final_run only:

```powershell
.\.venv\Scripts\python.exe -m pytest -q --basetemp .pytest_cache/v3-final-20261107
.\.venv-benchmark-v3\Scripts\python.exe -m pytest tests/benchmark_v3/test_modernbert.py -q --basetemp .pytest_cache/v3-modern-final-20261107
.\.venv\Scripts\python.exe -m src.benchmark_v3.verify --final
```

Observed suites: 257 passed, 1 skipped in 7.50s; 20 passed in 4.98s. Original environment lacks Torch; dedicated suite exercises actual pinned tokenizer/classifier and training guards. No failing tests remain.

The verifier reconstructs raw source/eligibility/rewrite approvals, checks exact model and artifact hashes, split/family/source isolation, train-only TF-IDF, lexical prediction reproduction, cached ModernBERT bindings, C0 equality and paired deltas. It checks all 228 final eligibility decisions, 246 actual requests, detector-blind payloads, 10 figures and 16 tables. Historical inventory: 1,044 files unchanged.

Earlier independent numerical ModernBERT replay concerned the intermediate corrected_run, not final_run. Do not transfer its 34/194/82 denominators to final results. Final model tests and hash-bound caches are verified separately.

Independent review identified protocol/adjudication binding gaps and a genuine payee-template leak; regressions and separate refits addressed them. Full final eligibility review then excluded 33 language/context cases without flipping labels. Preserved prior runs do not supply current results. Green tests do not provide independent human truth or meet the balanced sample target.
