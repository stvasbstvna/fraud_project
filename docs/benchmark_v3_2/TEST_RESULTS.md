# Final engineering and evidence verification

Fresh full repository command:

```powershell
.\.venv\Scripts\python.exe -m pytest -q --basetemp .pytest_cache/v32-full-final-20261107c
```

Observed **279 passed,1 skipped in16.29s**, exit0. Torch is intentionally absent from the original environment. Dedicated actual-model checks:

```powershell
.\.venv-benchmark-v3\Scripts\python.exe -m pytest tests/benchmark_v3/test_modernbert.py -q --basetemp .pytest_cache/v32-modern-integrity-20261107
```

Observed **20 passed in5.78s**, exit0. Independent frozen ModernBERT replay recomputed all26 probabilities: maximum absolute difference **0.0**. No fitting occurred.

The first full-suite attempt found a test-module name collision with legacy test_analysis.py. Adding an isolated v3.2 test package fixed collection; no tests were weakened. Matplotlib boxplot keyword compatibility was fixed before research plotting. A fixture newline mismatch was corrected to explicit UTF-8 LF bytes matching the production immutable writer.

New tests cover immutable outputs, nested detector-feedback keys, exact external prompt and raw-response hashes, absent registry entries, complete-case definition, duplicates, confidence/preservation gates, legacy and typed placeholders, source text/provenance binding, no technical-generation-failure quality retry, keyed distance alignment, paired analysis, zero-primary/empty-class support, model contrasts, and exact figure datasets/metadata. Test messages are isolated fixtures, never research observations.

Independent code review identified source packet-to-candidate binding, positional distance joins and technical-failure-as-quality-retry gaps. These were corrected before generation/scoring, with regression checks. Final independent review verified all105 run output hashes and3,510 result-index coordinates, with no remaining must-fix issue. Independent visual/data review found all12 figure bundles consistent; missing primary estimates are explicitly annotated, and the extreme is an unchanged false positive.

`verify` reconstructs every approved source and rewrite from raw provider responses, checks role snapshots and adjudication chains, literal invariants, C0 identity, fitting/template isolation, frozen model hashes, paired prediction identities and numerical lexical reproduction. `quality` checks the exact protected file list, all1,044 historical baseline hashes,118 protected v3 files, all run hashes, evidence-index cells and figure siblings. No changed historical files were found.

Green engineering checks do not meet the30+30 cohort target, supply independent human labels, or rescue zero complete trajectories. Scientific status remains **primary NOT RUN; exploratory available pairs only**.
