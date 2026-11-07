# Dataset presentation summary: corrected exploratory v3

The authoritative cohort is `data/benchmark_v3/corrected_run`. The original 231-family run is preserved but INVALIDATED after confirmed train/test template leakage. Current figures/tables are exclusively under `results/benchmark_v3/corrected_run`.

| Stage | Actual count |
|---|---:|
| Raw source records | 234,547 |
| Downloaded dataset groups | 8 |
| English SMS candidates | 209,827 |
| Financial/banking candidates | 37,063 |
| Exact duplicate excess removed | 13,625 |
| Unique financial candidates | 23,438 |
| Rights-eligible candidates | 12,247 |
| Fresh v3.1 source reviews | 707 |
| Initially approved reviews | 314 |
| Further policy exclusions | 2 |
| Approved rows before family exclusions | 312 |
| Template-family exclusions | 84 |
| Final independent representatives/families | 228 |
| Phishing | 219 |
| Legitimate | 9 |
| Real-source observations | 34 |
| Uncertain origin | 194 |
| Synthetic | 0 |

Real denotes observed non-synthetic source provenance, not verified human authorship. Four nominal source groups contribute: Gateway 194, Mendeley 27, NUS 6 and UCI 1. They are not asserted independent; upstream overlap exists. ExAIS/Super SMS/SpamHunter/SmishTank remain excluded from modeling for unresolved original reuse rights. Mendeley/UCI use CC BY 4.0, NUS has an authors' copyright-free declaration, Gateway has a repository MIT data release. See `docs/benchmark_v3/SOURCE_LICENSE_AUDIT.md`.

| Split | Total | Phishing | Legitimate |
|---|---:|---:|---:|
| Primary train | 160 | 153 | 7 |
| Primary validation | 34 | 33 | 1 |
| Primary held-out test | 34 | 33 | 1 |
| Separate source train | 29 | 21 | 8 |
| Separate source validation | 5 | 4 | 1 |
| Held-out Gateway source test | 194 | 194 | 0 |

Temporal test: NOT RUN because reliable message dates were inadequate. Sting9: zero rows, authentication/access blocked (401; documented dump 404), conflicting license pages. No raw Sting9 redistribution.

The desired minimum 300 phishing/300 legitimate messages was not reached. Generic spam was not automatically phishing; ham and money keywords were not automatically legitimate banking. Machine review is not independent human validation. Two personal-coordination controls were removed by policy recheck, and broader families repaired the discovered payee-registration leak. Because the prior test pool was already inspected, corrected results remain exploratory.

Primary robustness experiment: NOT RUN (minimum ten-control gate unmet). Separate supplement: 34 originals and 48 approved phishing variants, 82 scored rows/model; zero legitimate rewrites. Nine phishing frames have all four conditions. Stimuli were blind to original detector outputs but preceded corrected refitting, so their corrected reuse is retrospective. Seven upstream encoding flags remain disclosed without post-score text repair.

Presentation-safe conclusion: raw dataset size greatly exceeded the number of defensible independent financial controls. More licensed real institutional controls and independent human adjudication are needed before a confirmatory comparison.

Ten figures and 16 tables are available in `corrected_run`; figures 1–2 show source/class composition and acquisition-to-family attrition. The full report explains every figure and denominator.
