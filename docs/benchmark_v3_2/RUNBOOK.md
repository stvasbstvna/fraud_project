# Reproduction and integrity checks

The authoritative v3.2 run is `v32-expanded-001`. Scientific status: **primary completeness failed; exploratory available pairs exist**. Existing v3 `final_run` is read-only and remains unchanged.

Read-only reconstruction and checks, requiring existing source snapshots, API receipts and model artifacts:

```powershell
.\.venv\Scripts\python.exe -m src.benchmark_v3_2.verify
.\.venv\Scripts\python.exe -m src.benchmark_v3_2.quality
.\.venv\Scripts\python.exe -m pytest -q --basetemp .pytest_cache/v32-reproduction-suite
.\.venv-benchmark-v3\Scripts\python.exe -m pytest tests/benchmark_v3/test_modernbert.py -q --basetemp .pytest_cache/v32-modern-reproduction-suite
```

The verifiers do not call the API or train models. They accept identical receipts only and create content-addressed additive inventory revisions. `quality` reconstructs every evidence-index coordinate and checks all prior baseline/protected files. The actual Windows run stores some path fields with Windows separators.

Numerical inference replay:

```powershell
.\.venv-benchmark-v3\Scripts\python.exe -m src.benchmark_v3_2.score replay
.\.venv\Scripts\python.exe -m src.benchmark_v3_2.score evaluate
```

The ModernBERT replay recomputes all26 probabilities from frozen weights. The lexical evaluator recomputes all probabilities with the original environment to avoid scikit-learn version changes. Neither fits or tunes anything. Existing outputs must match byte-for-byte.

Paired analysis and figure replay:

```powershell
.\.venv\Scripts\python.exe -m src.benchmark_v3_2.analysis --matrix data/benchmark_v3_2/frozen/analysis_matrix.csv --predictions-dir results/benchmark_v3_2/predictions --output-dir results/benchmark_v3_2
.\.venv\Scripts\python.exe -m src.benchmark_v3_2.figures
```

No complete frame exists. Primary estimates, hypotheses and representative trajectory remain unavailable; figure03–06/08/09 explicitly annotate this. Figure07 is an available-pair exploratory fallback;10 is a separately selected extreme; M1/M2 describe all approved rewrites.

The original execution order was prepare → source packet → source A/B/J review → additional source packet/review → one bounded technical source recovery → documented source-policy exclusions/final C0 freeze → generation/one quality retry/A/B/J review → approved matrix freeze → manipulation → ModernBERT inference → three-model prediction export → analysis → figures → reports → verification/quality.

Do not rerun public-source API stages to seek preferred scores or completeness. The original failed requests and superseded source packets/freezes are evidence, not disposable caches. Any new generation model, prompt, eligibility rule or statistical-plan change requires a separate frozen version/run. The original SAP and registry remain immutable.
