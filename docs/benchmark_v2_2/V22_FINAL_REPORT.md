# Benchmark v2.2 — Controlled Linguistic Robustness Pilot

Final status: **V2.2 SOURCE COHORT INSUFFICIENT**.

The source audit was executed; the experiment stopped at the prospectively required source gate. There are **zero accepted source frames, zero generated variants, zero frozen benchmark rows and zero detector predictions**. This is a documented feasibility failure, not a completed robustness benchmark. There was no four-frame exploratory fallback.

V2.2 performed deterministic source feasibility checks. **Neither independent human annotation nor fresh LLM semantic review was performed.** The proposed downstream review mode is automated semantic review, which would itself remain a limitation relative to independent human annotation. No machine or human approvals were invented.

## 1. Why v2.1 failed

The preceding run had four sources, two synthetic legitimate controls, perfect source/label confounding and zero complete C0–C6 trajectories. C1 produced three copies, C2 four copies, and a broad event phrase used as an entity caused a questionable C6 rejection. Dates had been defanged as phone fragments. Available-pair score changes were real but could not rescue primary completeness or representative sampling. See `V21_FAILURE_ANALYSIS.md` for all 14 failure-to-prevention mappings and exact historical evidence inspected.

## 2. Exact corrections made

All additions are isolated under `benchmark_v2_2` in configs, data, docs, src, results and tests. New tested controls cover typed endpoint/account/reference redaction with protected ordinary dates/times/amounts; institution-span precision; non-action notification acceptance in typed semantic rules; C1 lexical-change screening; C2 already-direct/no-action triage; primary-core completeness independent of C2/C3; source minimum, diversity, class-specific source share, synthetic share, provenance and overlap gates; detector-feedback rejection; score-independent one-quality-retry rules; scoring preconditions; immutable output writes; historical hash verification; and exact-message lineage detection.

The existing Python environment and pure v2.1 normalization/similarity helpers are reused without modifying their files or numerical thresholds. Prior outputs are references for overlap checking, never transferred v2.2 approvals or observations. Original public releases were retrieved afresh into separate snapshots. Institution extraction is still a candidate hint until fresh semantic review; tests do not turn that hint into truth.

Prospective v22.1 condition prompts/configuration are saved, including C1 >=2 meaningful substitutions and one predefined quality retry. They are **not prevalidated or executed**. The downstream provider orchestration, successful source selection/freezing, generation, rewrite review, benchmark freezing, scoring and inference paths have not been implemented as a completed runnable experiment in this failed-source run. Tested helper gates and planned schemas must not be described as end-to-end success.

## 3–6. Source cohort, controls, distribution and families

The audit read 81,738 original/local message rows across six input groups (duplicates included), retaining 23,731 broad financial/known-institution candidates. Two source-audit tables and the row-level CSV retain the actual evidence. Of 23,105 preliminary rule-clear rows, 23,005 positive candidates were not fully family/contamination screened; these are not eligible or approved sources.

| Input source | Rows actually read | Broad candidates |
|---|---:|---:|
| Mendeley-SMISH v1 | 5,971 | 168 |
| UCI SMS | 5,574 | 99 |
| SMS-Gateway pinned release | 68,029 | 22,701 |
| Newly discovered Mendeley financial scams v2 | 523 | 213 |
| Local SmishX | 1,200 | 109 |
| Historical synthetic anchors | 441 | 441 |

Control preflight screened 400 ham/synthetic candidates against 2,778 train/validation/prior references. One hundred rule-clear ham rows remained, 50 Mendeley and 50 UCI, spanning 49 candidate families. **43 Mendeley rows have original-text SHA-256 identical to UCI**; they are UCI lineage, not independent Mendeley evidence. Remaining lineage-family capacities are 48 UCI and seven potentially independent Mendeley families. Family overlap across groups is deliberately not subtracted from the optimistic capacity.

With no source lineage above half a class, a class can include at most seven UCI cases alongside those seven non-UCI cases: **at most 14 controls, below the minimum 16**. This assumes every candidate is genuine banking ham and passes review; actual validity can only lower capacity. None of 187 historical synthetic controls survived prior-benchmark overlap screening, so synthetic augmentation cannot help this run.

The final accepted cohort is empty: phishing 0, legitimate 0, real legitimate 0, synthetic legitimate 0, final source groups 0/0, final template families 0. The number 14 is an optimistic bound, not a selected or validated cohort.

The new financial dataset contains 523 scam/ham messages (310/213), licensed CC BY 4.0. Its CSV lacks per-row SMS/chat/email channel; all 213 broad candidates remain on HOLD, including 64 ham rows. SmishX retains unresolved upstream-rights/training concerns. Unknown provenance or channel was not silently resolved by SMS-like wording. Public nonsynthetic-source candidate flags are not verified human authorship or bank authenticity. Full evidence, attributions, additional discoveries and scoped limitations are in `DATA_PROVENANCE.md`.

## 7. Label review

Fresh semantic source reviews: **0**. Because the source-capacity bound already fails, paying for A/B reviews cannot produce a sufficient cohort. No prior v2.1 review was imported. Ham remains a candidate label, spam never becomes phishing automatically, and the new collection's scam label requires banking/phishing review. Two-context typed source decision rules are tested but unexecuted. Agreement/adjudication statistics are NOT AVAILABLE.

## 8. Condition eligibility

Primary core is C0/C1/C4/C5/C6; secondary action conditions are C2/C3. Deterministic triage marks already-direct C2 as `already_direct` and no-action sources as `no_action`; unresolved cases require semantic eligibility review. No final cohort exists, so measured C2/C3 eligible N and primary eligibility rates are **NOT RUN**, not zero-rate results. Ineligible secondary conditions do not invalidate an otherwise complete core.

## 9–14. Prompt pilot, generation, retries, rejection, completeness and manipulation

The required 4+4 prompt prepilot did not run because accepted sources must be frozen first. C1 unchanged rate and C4/C5/C6 approval rates are **NOT AVAILABLE**. Generated variants 0; quality retries 0; rewrite approvals/rejections 0/0 (no review denominator). Primary-core and action complete-case counts are 0. No manipulation observations or condition-separability results exist. The prepilot thresholds (<10% C1 unchanged, C4/C5 >=80%, C6 >=75%), main approval gates (75/80/75/70%) and minimum 12+12 core cases remain unchanged prospective requirements.

Only `data/benchmark_v2_2/frozen/source_cohort.csv` with headers and a manifest explicitly marked `NOT_FROZEN_SOURCE_COHORT_INSUFFICIENT` were created. Primary/action benchmark CSVs were not created as fake freezes. An empty file carrying a failed manifest is not an accepted source freeze.

## 15–23. Detector, transition, control, distance, action, model, source and inference results

LR results: **NOT RUN**. RF results: **NOT RUN**. Threshold crossings, FPR, new/recovered false positives, distance associations, action-expression effects, model differences, source effects and statistical inference are **NOT RUN**. There are no v2.2 probabilities or p-values. Zero predictions must never be interpreted as zero effect.

Historical LR/RF artifacts were hash-verified without fitting or scoring. LR SHA-256: `84ba84863ce9a8fd757cd4e9babc6dacf39496223299a06df0054f94ca688fcc`. RF: `99c4a06e7ad52ff000c0a1d8818ca61cdc268d929a1a970e79d74b6e0c38b4fc`. Historical v2.1 detector observations remain historical; none is relabeled v2.2.

Twelve requested result table schemas (CSV/Markdown) are explicitly marked NOT RUN and contain no empirical rows. Two supplementary tables report actual source lineage/capacity; `source_audit_counts.csv` provides the detailed audit counts. Scientific figures: **0**. All seven requested figure slots are marked NOT AVAILABLE. No extreme or representative trajectory was selected.

## 24. Limitations

The feasibility conclusion is scoped to the financial-keyword/known-institution candidate pool from the audited sources, not every possible banking SMS or every existing dataset. Strict prior overlap, channel and rights requirements restrict available data. Mendeley/UCI contain many casual financial references; even the 14-case bound assumes more bank authenticity than is established. Treating all seven unmatched Mendeley families as independent is deliberately optimistic. Further upstream lineage resolution could reduce capacity. Positive-family screening was short-circuited after the control-capacity failure; positives are preliminary, not contamination-clear. No LLM review or linguistic manipulation has been empirically validated in v2.2.

## 25–27. Claims and scaling

Supported claim: a source-first audit identified that nominal dataset diversity exaggerated independent control availability; even an optimistic bound of 14 cannot meet the specified 16-control minimum under class-specific source caps. V2.2 correctly stopped before generation and scoring.

Unsupported claims: successful v2.2 benchmark, approved 14-source sample, real banking control cohort, validated prompts, measured detector robustness/vulnerability, condition effects, causality, significance, human/expert annotation or complete end-to-end implementation.

**Scale to full benchmark: NO.** Obtain independently supported, licensed English banking SMS controls with row-level channel/label provenance and enough nonoverlapping source groups. Resolving channel provenance for the new mixed collection or provenance/rights for the documented banking workbook may help; neither is already approved. Re-run source review/balance/freeze, then implement and execute the gated prompt prepilot and downstream experiment. Do not lower gates, silently relabel casual ham, or refill with legacy synthetic templates.

## Scientific questions 1–9

Questions 1–8 (largest primary effect, distance response, recall, crossings, control FPR, LR/RF agreement, independent directness effect, cross-source consistency): **cannot be answered because no v2.2 benchmark was frozen or scored**. Question 9 (is scaling justified): **NO**, because the source feasibility gate failed. This is a source-design conclusion, not a detector-performance conclusion.

## Verification and reproduction

The final suite and integrity receipt are recorded in `results/benchmark_v2_2/verification.json` and `TEST_RESULTS.md`. The historical inventory contains 979 files; all remain byte-identical. Independent review identified endpoint/fact-overlap and keyword-screen limitations; endpoint priority was corrected with failing-then-passing regressions, institution-only screening broadened, and the stopping claim explicitly scoped. A follow-up review confirmed the lineage-capacity bound. No dependency installation, private inbox access, external message, commit or push occurred.

```powershell
.\.venv\Scripts\python.exe -m src.benchmark_v2_2.run --offline
.\.venv\Scripts\python.exe -m src.benchmark_v2_2.verify
.\.venv\Scripts\python.exe -m src.benchmark_v2_2.status_artifacts
.\.venv\Scripts\python.exe -m pytest -q --basetemp .pytest_cache/v22-final-full-suite-b
```

The audit deliberately exits nonzero with `V2.2 SOURCE COHORT INSUFFICIENT`; this is the expected scientific gate, not a credential failure. `run` without `--offline` downloads missing original public snapshots only; it does not call an LLM or detector. Offline reruns require saved snapshots, verify original hashes, and refuse changed existing outputs. The verifier exits successfully only after historical/model/input integrity and source bound reproduce. Future source additions must receive a new isolated run/versioned evidence directory rather than overwrite this failed run.
