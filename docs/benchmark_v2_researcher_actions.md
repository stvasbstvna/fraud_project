# Benchmark v2 researcher actions

1. Review source options in `docs/benchmark_v2_FINAL_DECISION_PACKAGE.md`; record the selected strategy there.
2. Add evidence for every permitted source to `data/benchmark_v2/source_manifest.csv`; do not set final authorization without documentation.
3. Approve/modify/reject the inactive generator in `docs/benchmark_v2_FINAL_DECISION_PACKAGE.md`; after mentor sign-off, implement the approved values in `configs/benchmark_v2_generator.yaml` and `configs/benchmark_v2.yaml`.
4. Review power assumptions with the mentor using `docs/benchmark_v2_power_decision.md` and the final decision package.
5. Record minimum meaningful and expected effects for H1–H4 in `docs/benchmark_v2_FINAL_DECISION_PACKAGE.md`.
6. Select target power, discordance/dependence assumptions, phishing N, legitimate precision/N, and attrition rule in the same file; synchronize approved values into `configs/benchmark_v2.yaml` and `configs/benchmark_v2_freeze_register.yaml`.
7. Freeze event/tactic/action/source distributions and generator assignment/crossed-subset choice in `configs/benchmark_v2.yaml`.
8. Give `data/benchmark_v2/pilot/pilot_review_sample_C3_softened.xlsx` independently to Reviewer A and Reviewer B using `docs/benchmark_v2_pilot_review_instructions.md`.
9. Preserve both completed review files; calculate agreement and the approved C3 manipulation check without detector fields.
10. Adjudicate disagreements/failures using `docs/benchmark_v2_adjudication_protocol.md`; preserve original judgments.
11. Record pilot completion, attrition evidence, agreement, and manipulation decision in `docs/benchmark_v2_FINAL_DECISION_PACKAGE.md` and `docs/benchmark_v2_freeze_signoff.md`.
12. Obtain researcher/faculty/provenance/review signatures in `docs/benchmark_v2_freeze_signoff.md`.
13. Finalize the prompt only through the transition in `docs/benchmark_v2_draft_transition.md`; preserve the draft and create a versioned final file/hash.
14. Re-run readiness; do not remove `DRAFT_DO_NOT_GENERATE` unless every preceding gate passes.

## Prepared post-approval sequence — do not run early

Replace the example effect/discordance/N below only with signed values:

```powershell
.\.venv\Scripts\python.exe .\analysis\benchmark_v2_power_simulation.py --effect 0.04 --discordance 0.10 --sample-sizes 750 --simulations 10000 --output-dir .\results\benchmark_v2\power\approved
.\.venv\Scripts\python.exe .\scripts\check_benchmark_v2_freeze_readiness.py
.\.venv\Scripts\python.exe -m pytest -q
```

Then, in order: finalize the authorized source manifest; activate the signed generator block and assignment weights; finalize/version/hash prompts; import/preserve completed pilot review and adjudication; remove the draft lock only if the checker prerequisites are satisfied; require `FULL_FREEZE_READY`; build the freeze package; rerun tests; hash frozen artifacts; and only then create a separate signed generation authorization.

Do not run `build_benchmark_v2_freeze_package.py` as a claim of full freeze while readiness remains blocked; its current output is intentionally a freeze candidate.
