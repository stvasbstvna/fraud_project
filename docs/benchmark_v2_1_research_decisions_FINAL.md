# Benchmark v2.1 Research Decisions

The researcher instructed the project to proceed without additional interactive decision requests. The following choices are therefore fixed prospectively for the next benchmark build and may be revised only before detector evaluation, with the revision documented and the benchmark version incremented.

1. **Confirmatory source strategy:** researcher-authored synthetic anchors; real-world corpora exploratory only.
2. **Generator candidate:** OpenAI `gpt-5.4-mini-2026-03-17`.
3. **Generation parameters:** temperature 0.2, top_p 1.0, one output/job, max two attempts, max 500 output tokens, no detector context.
4. **Linguistic design:** C0-C6 dose-response conditions as defined in the protocol.
5. **Primary scientific focus:** sensitivity to controlled linguistic distance, not purposeful detector evasion.
6. **Working meaningful binary effect:** 0.04 absolute change; treated as a design assumption.
7. **Working discordance assumption:** 0.10; treated as a design assumption.
8. **Target family power:** >= 0.80, with 0.85+ preferred when feasible.
9. **Working final N:** 750 phishing frames; 500 legitimate controls.
10. **Agreement statistic:** Cohen's kappa for categorical validity fields. Weighted kappa is reserved for any ordered multi-level directness scale.
11. **C3/C6 manipulation threshold:** >=80% of valid paired ratings identify the softened condition as less direct than C2.
12. **Core preservation threshold:** >=95% semantic/action preservation; >=98% entity/channel/safety preservation.
13. **Attrition rule:** estimate from completed pilot human review before full generation; never revise using detector results.
14. **Freeze rule:** generation remains blocked until human review and readiness checks pass.
