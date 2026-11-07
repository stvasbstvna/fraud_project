# Dataset presentation summary

Eight source groups supplied 234,547 raw records. Heuristic English screening retained 209,827 candidates; financial screening retained 37,063. Exact duplicate excess was 13,625, leaving 23,438 unique financial candidates and 12,247 rights-eligible candidates. Screening is not semantic validation. Sting9 supplied zero rows: actual 401 export responses, 404 documented dump and conflicting license statements are preserved in STING9_ACCESS_AND_LICENSE_AUDIT.md.

Final source counts: Gateway 167, Mendeley 24, NUS 4. These are nominal dataset groups, not independent populations. Original row IDs, original annotations, duplicate origins and reviewed labels remain distinct. Origin accounting is 28 real-source observations, 167 uncertain-origin observations and zero synthetic observations. Real-source does not establish authenticated bank authorship.

SOURCE_LICENSE_AUDIT.md and provenance/upstream_rights_evidence.json retain original evidence. Mendeley and UCI state CC BY 4.0; Gateway releases repository data under MIT. NUS authors declare copyright-free unlimited use, which is not an invented CC0 grant. SmishTank, SpamHunter, Super SMS and ExAIS remain excluded from modeling for unresolved reuse evidence. Aggregator availability does not replace original rights.

707 source candidates received fresh v3.1 review; 314 initially passed and two policy exclusions left 312. Conservative family grouping and two further coordination exclusions produced an intermediate 228-family cohort. A subsequent detector-blind eligibility audit reviewed ALL 228 representatives: 195 retained, 33 phishing candidates excluded for language/context, no labels flipped. All nine legitimate controls survived. ASCII screening alone had admitted non-English messages. The final audit used 26 actual A/B/J requests; all decisions and raw evidence are bound in final_eligibility_audit. This post-score population correction makes final inference exploratory.

A genuine Shijo/Sinco payee-registration train/test template leak invalidated the original 231-family run. Its artifacts remain preserved. Broader source-only normalization fixed the known optional-suffix pattern. The intermediate corrected_run was later superseded by final English/financial eligibility. Only final_run supplies current results; undetected semantic dependencies remain possible.

195 family representatives: 186 phishing and nine legitimate; 28 real-source, 167 uncertain-origin, zero synthetic. The desired 300+300 target is NOT MET. Acquisition volume cannot substitute for rights-cleared and policy-valid controls.

Primary train/validation/test: 137/29/29, with phishing/legitimate counts 130/7, 28/1 and 28/1. Separate source experiment: train 24 (16/8), validation four (3/1), test 167 Gateway phishing messages. All three methods share each experiment’s cohort. The earlier test pool was inspected before correction; this is not an untouched confirmatory holdout.

The final verifier reconstructs source approvals, full eligibility coverage, exact/family isolation, pooled-origin source exclusion, train-only TF-IDF, frozen model hashes, detector-blind payloads, cached predictions and paired deltas. 1,044 historical files remain unchanged. Protocol, correction plan, eligibility plan/decision and cohort hashes bind the final freeze. No rewrite enters model fitting.

Nine legitimate training-population controls, one legitimate test control, machine labels, uncertain source origins, possible template dependence, source imbalance, reused test pool, post-score eligibility correction and selective rewrite attrition limit inference. Seven complete phishing trajectories are not seven representative trajectories of both classes. Tiny imbalanced training data cannot fairly establish ModernBERT’s broad capacity. No deployment recommendation follows.

Authoritative evidence: data/benchmark_v3/final_run and results/benchmark_v3/final_run. Source review is automated; 300+300 target unmet. See docs/benchmark_v3/FINAL_REPORT.md for all 25 reporting items.
