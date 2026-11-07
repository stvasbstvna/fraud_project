# Pilot execution checkpoint — 2026-11-06

**PILOT NOT READY.** This run continues the existing infrastructure; it does not rebuild or authorize unreviewed data.

Ready: preserved 441-candidate canonical pool, fixed C0–C6 prompts, frozen model hashes/vectorizers, blinded generation adapter, objective validators, human-review/import and paired analysis/reporting code. Existing 48-candidate file is a planning selection, not a template-controlled or approved pilot.

Blocked: no completed independent source review, no approved C0 cohort, inactive generator configuration, no completed generated/rewrite-review/frozen/evaluated pilot. Model availability is unverified; credential presence is not assumed or exposed. No scores may be used in selection.

This run will: audit original-source rows and licenses; assign deterministic template families with placeholder/entity/number normalization and lexical/structural similarity; screen against training/validation templates; select at most 24/24 diverse candidates without modifying the master pool; create separate Stage A source-review forms and an explicit readiness/attrition report. It will proceed through generation only if source approvals and provider configuration genuinely permit it. Missing human review is a real external boundary; no synthetic approval, missing text, frozen evidence or empirical figure will be invented.

Initial preservation snapshot: `PILOT_BASELINE_INVENTORY.csv` contains 440 existing non-cache files, excludes `.env` and itself. Only `results/benchmark_v2_1/PRESENTATION_SUMMARY.md` is authorized for update; its prior bytes will be archived first. Existing code/config/prompts/data/results otherwise remain untouched.

Early access findings: the original Mendeley landing page/license and public file listing are accessible using the site's documented endpoint, despite initial incorrect endpoint failures. `Dataset_5971.zip` has publisher-confirmed SHA-256 `9bbf3188fdad81495d8e82825648b9b63b53fc86841a3d26c02629990b233cc3`. Gateway original repository and UCI original archive are accessible. Source availability does not imply row label approval.

## End-of-run checkpoint

Original-source row audit and final template-controlled candidate selection executed. 1,287 external financial audit rows plus 441 preserved master candidates yielded 29 selected review candidates in 29 families: 24 phishing-labelled/5 legitimate-labelled. 71 train/validation template matches excluded. At least 19 more control candidates are needed; all five existing proposed controls still require validation. The reduced queue is source-imbalanced (Gateway 17/29) and cannot be treated as an approved reduced pilot.

58 Stage A review assignments prepared; 0 source approvals, 0 generated rewrites, 0 Stage B observations, 0 complete frames/final condition rows. Generation blocked at the missing-human-review boundary. Existing prompts/configuration/models unchanged. Full tests: 159 passed. Current report: `PILOT_FINAL_REPORT.md`. Exact next action: two independent reviewers complete `data/benchmark_v2_1/review/pilot_source_review.csv`, then run `python -m src.benchmark_v2_1.pilot_review --reviews data/benchmark_v2_1/review/pilot_source_review.csv`; also resolve the missing-control/source-balance design before generation. **PILOT NOT READY.**
