# Final verification — 2026-11-06

Full repository suite:

```powershell
.\.venv\Scripts\python.exe -m pytest -q --basetemp .pytest_cache/v22-final-full-suite-b
```

Observed result: **201 passed in 6.95s**, exit 0. This includes 29 new v2.2 tests and 172 existing tests. No existing test was weakened or edited. New tests were observed failing before their corresponding implementation/fixes; the actual legacy-reference schema mismatch, endpoint/date collision and source-lineage capacity inflation received regressions.

Coverage includes dates/times/amounts versus phones; account/transaction IDs, URLs/emails, arbitrary domains and IP endpoints; institution/event span separation; already-direct/no-action C2; C1 copies; core completeness without secondary conditions; source minima/diversity/share/confounding/synthetic limits; provenance and contamination; scoring prerequisites; detector-blind payloads and score-independent retries; exact-threshold family propagation; mixed-channel hold; immutable writes; typed control review with NONE action; lineage-capacity bound; historical tamper/deletion detection.

`python -m src.benchmark_v2_2.verify` observed **979 historical files checked, zero changed**, four original public message snapshots matching expected SHA-256, unchanged LR/RF hashes, source audit/failed manifest hashes consistent, reproduced optimistic capacity 14 <16, no LLM result caches and no detector prediction outputs. The verification receipt is `results/benchmark_v2_2/verification.json`.

`python -m src.benchmark_v2_2.run --offline` reproduces the expected nonzero scientific stop `V2.2 SOURCE COHORT INSUFFICIENT`. This is not a failed software test or unavailable credential. Exact duplicate-origin evidence and all counts come from saved source data, not reviewer speculation.

Independent read-only review found two substantive issues: nested date/time protection could leave URLs live, and the original keyword screen omitted known-institution-only notifications. The former was fixed by endpoint priority with four failing-then-passing regression cases; the latter by the full known-brand screen and explicit scope limitations, also with a failing-then-passing TSB case. Follow-up review confirmed the new 14-control lineage upper bound and honest zero downstream counts. Preliminary positive rows are explicitly not called family/contamination cleared.

No scientific prompt pilot, preservation-rate experiment, semantic-review agreement study or detector test was performed in v2.2. Software tests are not empirical benchmark validation.
