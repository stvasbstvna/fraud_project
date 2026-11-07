# Reproduction and current artifacts

Use final_run. Original run is invalidated for template leakage; intermediate corrected_run is superseded after full language/financial eligibility review. All prior evidence remains preserved.

```powershell
.\.venv\Scripts\python.exe -m src.benchmark_v3.verify --final
.\.venv\Scripts\python.exe -m pytest -q --basetemp .pytest_cache/v3-reproduction-final
.\.venv-benchmark-v3\Scripts\python.exe -m pytest tests/benchmark_v3/test_modernbert.py -q --basetemp .pytest_cache/v3-modern-reproduction-final
```

Existing frozen evidence needs no new API calls. The verifier writes only its reproducible receipt. Do not overwrite research freezes or call generators again to improve outcomes.

Final dispatcher: `python -m src.benchmark_v3.final_run STAGE`. Available stages include prepare, lexical, modern_train, modern_infer, evaluate, C_infer, C_evaluate, statistics and reports. Run modern_train/modern_infer/C_infer in the dedicated .venv-benchmark-v3 environment; other stages in the original .venv. Existing outputs use immutable guards; a clean replay requires an isolated copy with occupied outputs handled according to stage guards, not deletion of preserved evidence.

Source acquisition/reviews and original blinded rewrite calls remain under data/benchmark_v3/provenance, review, final_eligibility_audit and robustness. Final cohorts/models/results are under their final_run subdirectories. Review/generation must never receive detector probabilities. No temporal or balanced primary-C result exists.
