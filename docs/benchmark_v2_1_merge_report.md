# Benchmark v2.1 patch integration report

Date: 2026-08-28  
Repository: newest local `fraud_project` working tree  
Patch SHA-256: `0f3f64322e124fb24e20360600a3248ce689a5a93686b5344046cfc29317d7c7`  
Integration status: **PATCH INSPECTED — SAFE ADDITIVE MERGE APPROVED**

## Search performed before merge

The workspace, Codex attachment store, and `C:\Users\sabin\Downloads` were searched for:

- `benchmark_v2_1_patch_only.zip`
- `fraud_project_benchmark_v2_1_expanded.zip`
- `pilot_review_sample_v2_1.xlsx`
- filenames containing `v2_1` or `v2.1`

The patch was subsequently downloaded to the repository root and extracted only into `_v21_patch_inspect` for comparison. Existing `benchmark_v2_protocol_review*.zip` files predate v2.1 and are not substitutes.

## Overlap classification

| Scope | Classification | Action |
|---|---|---|
| Benchmark v1 data, results, and model binaries | local authoritative / preserve | untouched |
| Current Benchmark v2 C0–C3 protocol, pilot, decision package, readiness and freeze candidate | local newer state / preserve | keep in existing `benchmark_v2` paths as historical/current v2 work |
| V2.1 protocol, prompts, scientific rationale, review instructions and decisions | patch newer / compatible additive | merge as versioned v2.1 documents; retain local approval/safety history |
| 1,250 C0 anchors and 8,750 C0–C6 condition rows | patch additive | merge under isolated `data/benchmark_v2_1`, never replace v2 pilot/final data |
| 48-frame / 336-row v2.1 pilot and workbook | patch additive | merge under isolated v2.1 paths; decisions remain blank |
| Patch generator config | conflict requiring manual merge | preserve patch candidate in a v2.1 config; keep local richer v2 retry/logging config untouched |
| Patch readiness and freeze builders | conflict requiring manual merge | rename to v2.1 scripts and isolate paths/results; do not overwrite newer local v2 scripts |
| Patch confirmatory helper | methodological conflict | do not accept unchanged: it tests 12 C0 contrasts rather than the previously declared seven-test family; revise/test before any evaluation |
| Patch distance helper | compatible additive with naming/formula documentation required | isolate as v2.1; use detector-independent corpus TF–IDF; align output names with v2.1 schema |
| Patch generation runner | compatible concept but unsafe exception handling/checkpointing | isolate and harden before any authorized use; dry-run only now |
| Patch `__pycache__`/`.pyc` | generated historical artifacts | never merge |
| Historical protocol-review ZIPs | historical / do not merge | untouched |

## Conflict policy once the patch is attached

For every patch member, compare normalized path, SHA-256, modification context, and semantic version. Additive `benchmark_v2_1` paths may be integrated after validation. Any patch file overlapping current v2 files must be manually merged so current safety rules, C3-softened semantics, approval gates, provenance work, and newer tests are retained. Never copy an archive root over the repository.

## Consequence

The exact C0–C6 definitions can now be integrated from the patch. Patch prose that says decisions are “final” is treated as prospective design metadata, not evidence of completed human review or permission to generate. Technical readiness may be reported separately, but full freeze remains blocked by pilot generation, two human reviews, agreement/adjudication, manipulation success, final review, and final dataset creation.

## Integration result

Twenty-two relevant patch files were merged additively and renamed into isolated v2.1 paths. No `__pycache__` or `.pyc` was copied. Current v2 configuration, readiness scripts, data, and freeze candidates were not overwritten.

Post-merge verification:

- 1,250 full frames: 750 phishing, 500 legitimate;
- 8,750 unique C0–C6 condition rows;
- 48 pilot frames and 336 condition rows;
- 288 unrun pilot C1–C6 jobs;
- zero duplicate variant IDs, incomplete condition sets, or live URLs;
- synthetic source hash/authorization metadata validates;
- review workbook contains 336 blank review rows and no detector fields;
- generator remains inactive and unauthorized;
- dry-run made no API call;
- 109 canonical tests pass.

The audit added one honest technical blocker absent from the patch's saved readiness snapshot: `confirmatory_analysis_plan_conflict=1`. The patch helper's twelve pairwise tests conflict with the existing seven-test Holm family. This is documented in `docs/benchmark_v2_1_confirmatory_family_decision.md` and must be resolved before generation.
