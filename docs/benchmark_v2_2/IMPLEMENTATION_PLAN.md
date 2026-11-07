# Benchmark v2.2 implementation plan

> For agentic workers: use superpowers:executing-plans. Execution is explicitly requested by the user's supplied specification; do not pause for another plan approval.

Goal: implement and execute an isolated, validity-gated controlled linguistic pilot. The binding spec is the user attachment `959d4655-4a0d-4a2b-95dd-90bc947f0d8d/Pasted text.txt`.

Architecture: additive Python namespace, immutable input/output hashes, typed safety transformations, source-first gates. Historical files remain read-only. No output from v2.1 becomes a v2.2 observation or approval. Use original public source releases where possible; historical data are screening references only.

Approach ruling: use the existing Python environment and fixed detector artifacts, but new semantic fields and new source gates. Reusing the v2.1 four-frame partial experiment is expressly excluded by the spec. No commit or push.

## Global constraints

Minimum source cohort 16+16; target 24+24. Synthetic legitimate fraction <=25%. At least two independent groups per class, target three; no group >50% of either class. Require at least one source contributing both labels (operational prevention of perfect source-label confounding). One source per template family. Training/validation and prior-benchmark family overlap excluded. Confidence >=0.80; no detector feedback during selection, generation or review.

Primary core C0/C1/C4/C5/C6; C2/C3 separately eligible. Prompt prepilot 4+4 only AFTER acceptable frozen sources. Initial generation plus at most one prespecified quality retry; none based on scores. Main gate >=12+12 complete cases and C1/C4/C5/C6 approval >=75/80/75/70%. A failed source gate stops all downstream generation and scoring rather than starting another tiny exploratory run.

## Tasks

- [x] Audit v2.1 reports, actual outputs, prompts, reviews, figures and failure diagnostics; record prevention mechanisms.
- [x] Snapshot historical inputs; implement typed defanging and precise institution validation with red/green regression tests.
- [x] Implement source/core/eligibility/retry/scoring gates with regression tests for each specified failure mode.
- [x] Re-audit available local source groups and their inventory; retrieve original licensed Mendeley/UCI/Gateway releases and new provenance-safe discoveries. Record labels/channel/authorship separately and reject unsupported banking/legitimacy claims. Unavailable or held sources are documented, not falsely counted as read/accepted.
- [x] Screen control templates against train/validation and prior benchmarks without relaxing v2.1 similarity thresholds. Compute an optimistic source-capacity bound before paying for semantic review. The bound failed at 14 <16 after exact source-lineage matching; full positive clustering was not needed or claimed.
- [ ] If capacity permits, perform fresh independent machine source reviews, select/freeze acceptable balanced source cohort, implement and execute prompt prepilot then main generation/review/manipulation/freeze/scoring in order. Otherwise mark these dependent stages NOT RUN, not complete, and do not implement a fake successful path.
- [x] Produce final 27-point report, presentation summary, source/status tables; no scientific figures without sufficient frozen predictions.
- [x] Run full repository tests, historical hash comparison and independent code review; document exact blockers and remaining implementation.

Task six remains deliberately NOT RUN: the source gate failed. Downstream execution and its successful-path orchestration are not claimed implemented/complete. See `EXECUTION_LEDGER.md`, `V22_FINAL_REPORT.md` and `TEST_RESULTS.md`.

## Review focus

Mixed SMS/email collections without row-level channel cannot silently become SMS; synthetic detection must not rely on ham labels; all-ham banks with zero requested action remain legitimate candidates; dates and amounts must not be phone numbers; a public repository license alone does not cure training contamination or prove label truth. An optimistic capacity shortfall is a real stopping condition, not a completed experiment.
