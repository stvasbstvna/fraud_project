# HORIZONS 12-minute slide plan

Audience: broad research audience. Communication job: explain what was tested, what the preliminary evidence does and does not show, and why human-reviewed Benchmark v2 is the next methodological step.

## Main deck (10 slides)

1. **A harmless rewrite can test whether a smishing detector learned meaning or wording** — define smishing once: fraudulent SMS designed to induce an unsafe action. Open with the research question.
2. **The test changes wording while holding the message pair fixed** — paired original/rewrite design; same label, action, and identifiers; detectors frozen.
3. **The experiment blocks detector-guided optimization** — frozen split and models, defanged placeholders, no detector feedback to generation, safety checks, human review gate.
4. **153 safe rewrites completed human semantic review** — 153/156 completed, 3 safety-rejected, 153 approved and 0 pending.
5. **Preliminary recall changed by one phishing case per detector** — LR 98.6%→97.9%; RF 97.9%→97.2%; show `detector_performance.png`.
6. **The paired evidence does not establish degradation** — one detected→missed transition per model; both McNemar p=1.0; show `paired_transitions.png`.
7. **Probability sensitivity is not the same as classification failure** — mean confidence drops -0.0004 and -0.0003; both 95% CIs include zero; show confidence plot only as exploratory.
8. **Legitimate controls reveal a different limitation** — specificity LR 30%→20%, RF 0%→0%, but n=10; frame as false-positive/generalization weakness, not rewrite attack success.
9. **Benchmark v2 strengthens provenance, conditions, and human review** — authorized anchors, frozen prompts, documented generator pool, detector-blinded generation, complete C0–C3 approvals.
10. **The current conclusion is methodological, not adversarial** — v1 is human-approved, but its paired effect remains small and non-significant; stronger claims require preregistered v2 testing.

## Appendix

- A1. Frozen model comparison and baseline validation metrics.
- A2. Full paired metrics, confidence intervals, and McNemar tests.
- A3. Human-review rubric and approval/adjudication rules.
- A4. Benchmark v2 pilot disclaimer and provenance boundary.
