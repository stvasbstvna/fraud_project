# Benchmark v2.1 confirmatory-family conflict requiring pre-generation resolution

The patch adds C4–C6 and identifies dose response as central, but its analysis helper performs C0-versus-C1…C6 separately for both detectors: twelve McNemar tests. The existing preregistered v2 plan instead contains exactly seven tests: H1/H2/H3 for two detectors plus H4 interaction. Treating the patch helper as already frozen would silently change the multiplicity family and invalidate the existing power calculation.

No detector outcomes have been inspected. Resolve this before pilot generation so prompts, power, and analysis remain prospective.

## Option A — preserve the seven-test confirmatory family

Keep existing H1–H4 primary tests. Treat C4–C6 distance ordering, monotonic trends, and additional C0 contrasts as prespecified secondary/exploratory analyses with a separately declared correction family. This preserves the existing power basis but makes the new dose-response contribution non-primary.

- [ ] Approve Option A

## Option B — preregister a new v2.1 primary family

Replace the seven-test family prospectively with a smaller set of explicit dose-response tests rather than twelve redundant pairwise contrasts. Recommended structure for faculty review: one condition/distance trend test per detector, one detector-by-distance interaction, and only scientifically essential anchor contrasts. Freeze the exact endpoint, direction, effect scale, test count, cluster method, alpha allocation/Holm family, and rerun power simulation before generation.

- [x] Approve Option B — approved by the researcher before generation
- Exact family: H1/H2 common continuous/binary distance trends plus H5–H9 pooled nonredundant condition contrasts
- Design assumptions for sensitivity: 0.04 maximum FN increase; target standardized logit-distance slope profile; no detector-result input
- Multiplicity rule: one seven-member Holm family at FWER 0.05

## Prohibited resolution

Do not run all available pairwise tests and choose a family after observing detector results. The approved implementation uses two primary trend tests plus five scientifically nonredundant pooled contrasts. Detector interactions are prespecified exploratory model-comparison analyses. `FULL_FREEZE_READY` remains false until consistency, manipulation, generation, and human-review gates pass.
