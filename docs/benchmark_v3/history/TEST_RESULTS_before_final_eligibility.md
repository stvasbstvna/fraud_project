# Final verification

Authoritative results are under `corrected_run`. The original v3 run is preserved and invalidated for the discovered payee-template overlap.

```powershell
.\.venv\Scripts\python.exe -m pytest -q --basetemp .pytest_cache/v3-final-repository-suite-b
```

Observed: **255 passed, 1 skipped in 6.15s**, exit 0. The skipped test requires Torch, intentionally absent from the original environment. It is not a failed or omitted ModernBERT verification:

```powershell
.\.venv-benchmark-v3\Scripts\python.exe -m pytest tests/benchmark_v3/test_modernbert.py -q --basetemp .pytest_cache/v3-modernbert-root-final
```

Observed independently by the root agent: **20 passed in 4.48s**, exit 0. This includes actual pinned tokenizer/classifier loading, binary output shape and probabilities, train/test isolation, frozen-weight tampering rejection, protocol guards and immutable cached-training behavior. A real full-parameter CPU AdamW fixture and both corrected research fits were also executed; synthetic feasibility fixtures are never counted as research messages.

Source-parser tests cover all eight parsed schemas, raw label retention, unlabeled NUS and timestamp ambiguity, UCI tab structure, Gateway's two header variants, flagged legacy encoding and Git checkout line endings. Scientific guards cover label ambiguity, financial relevance, exact origins, rights-aware representative choice, family/source/temporal isolation, detector-blind payloads, class support, literal invariants, confidence, adjudication chains, exact IDs, UTF-8 evidence hashes, probability ranges, undefined one-class metrics, paired McNemar/Holm and small-control exact uncertainty. The actual Shijo/Sinco template leak has a regression and a preserved invalidated predecessor run.

`python -m src.benchmark_v3.verify` observed **1,044 historical files unchanged**, all eight parsed source files hash-matched, corrected source review and raw provider bindings verified, no exact/family cross-split witnesses, no Gateway origin in source fitting, train-only TF-IDF reconstructed exactly, model hashes verified, lexical probabilities reproduced, and C0/pairwise deltas consistent across corrected A/C. It also checks that corrected stimuli are exactly the held-out intersection of unchanged blinded stimuli. Receipt: `results/benchmark_v3/corrected_run/verification.json`.

Independent code review found prospective-configuration and adjudication-chain binding gaps; both received failing-then-passing regressions and were fixed. Manual/independent scientific review subsequently found a real optional-suffix payee-template leak and two policy-ineligible coordination controls. The original run was not silently patched: a new corrected freeze and unchanged-hyperparameter refits were executed before corrected scoring. Follow-up review found no remaining critical/important issue in current artifacts. This is not proof that no undetected semantic dependency remains.

All ten corrected PNG/SVG figures were visually checked in a contact sheet. Captions disclose actual denominators, machine labels, source-only scope, missing controls and available-pair attrition. No deployment, commit, push, private inbox access or Sting9 data redistribution occurred.

Fresh independent numerical replay also recomputed ModernBERT probabilities directly from corrected weights for all 34 primary rows, 194 source-test rows and 82 supplemental rows. Maximum absolute difference from each saved probability cache was **0.0**. This used the dedicated environment and no fitting or artifact modification.

Green tests establish implemented behavior and reproducibility. They do not meet the missing 300+300 sample target or create independent human ground truth.
