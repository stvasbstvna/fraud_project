# Benchmark v2.1 Controlled Linguistic Robustness Protocol

## Research question

How sensitive are TF-IDF-based banking-smishing detectors to controlled linguistic variation when malicious intent, requested action, entity, channel, destination, and safety state are held constant?

This protocol replaces the weaker framing "make a detector fail" with a preregistered robustness question. The objective is to measure whether increasing surface-form distance produces measurable changes in detector confidence or binary detection while semantic content remains stable.

## Design principle

The benchmark uses paired / repeated-measures semantic frames. Every condition derived from a frame must preserve:

- semantic intent;
- requested action;
- banking entity role;
- destination type;
- communication channel;
- phishing/legitimate label;
- safety state;
- defanged destinations.

Detector predictions are prohibited during generation, review, adjudication, and inclusion/exclusion decisions.

## Conditions

- **C0 — Anchor:** canonical researcher-authored safe/defanged realization.
- **C1 — Minimal lexical variation:** light paraphrase with similar syntax and directness.
- **C2 — Direct action realization:** requested action is stated explicitly.
- **C3 — Softened action realization:** same requested action as C2, expressed less directly. The action is not removed.
- **C4 — Natural-language normalization:** more fluent conversational wording while preserving action/directness category.
- **C5 — Strong semantic-preserving paraphrase:** larger lexical and syntactic change without changing intent/action/entities.
- **C6 — Combined high-distance realization:** combines lexical substitution, syntactic restructuring, naturalization, and softened directness while preserving all invariants.

C0-C3 remain directly comparable to the existing pilot logic. C4-C6 are added before final freeze to make linguistic distance an explicit experimental factor rather than optimizing against model outputs.

## Primary endpoints

The preregistered family is `bv21-dose-response-primary-v1`, defined in `configs/benchmark_v2_1_confirmatory_family.yaml` and `docs/benchmark_v2_1_confirmatory_analysis_plan_FINAL.md`.

1. Primary continuous trend: within-frame slope of clipped-logit phishing probability over detector-independent `combined_surface_distance`, averaged across the two frozen detectors.
2. Primary binary security trend: within-frame slope of the false-negative indicator over the same distance, averaged across detectors.
3. Five secondary-confirmatory pooled paired contrasts: C0–C1, C2–C3, C0–C4, C0–C5, and C0–C6.

Exactly these seven new dose-response hypotheses form one Holm family at FWER 0.05. Detector-by-distance interactions, individual-detector contrasts, recall/FNR tables, transitions, and alternative distance components are prespecified supporting/exploratory analyses.

## Secondary measurements

- token Jaccard similarity;
- normalized edit distance;
- TF-IDF cosine similarity computed independently of classifier coefficients;
- semantic-preservation review outcomes;
- model disagreement.

## Confirmatory safeguards

- frozen detector models only;
- no retraining or threshold tuning on Benchmark v2;
- no detector-guided rewriting;
- no selective regeneration after seeing outcomes;
- no detector-based exclusion;
- all planned confirmatory contrasts fixed before detector evaluation;
- multiplicity handled with the preregistered Holm family;
- null findings are retained and reported.

## Source strategy

The confirmatory benchmark uses **researcher-authored synthetic anchors** with fictionalized/placeholder banking entities and defanged destinations. This maximizes redistribution clarity and experimental control. Real-world datasets such as SmishX/SmishTank are retained for exploratory external-validity analyses only where their usage terms permit.

This choice improves control but reduces ecological validity. The limitation must be stated explicitly in reports and presentations.

## Sample-size decision

Research-design working target:

- phishing semantic frames: **750 final**;
- legitimate controls: **500 final**.

For phishing frames, the updated prospective simulation includes seven repeated conditions, two correlated detector outcomes, frame effects, continuous logit-score shifts, binary false-negative shifts, and Holm correction across the new seven-member family. Under the target profile (maximum FN increase 0.04, logit-distance slope −0.15, contrast logit effect −0.10), N=750 produced approximately 1.00 minimum primary power and 0.95 minimum power across all seven confirmatory members. N=500 produced approximately 0.994 and 0.84. N=750 is therefore retained to meet the preferred 0.90 all-family sensitivity under the target profile—not merely because it was previously proposed. Smaller-effect sensitivity remains explicitly uncertain.

For 500 legitimate controls, a specificity near 0.95 would have an approximate Wilson 95% interval half-width of about 0.019, giving roughly ±2 percentage-point precision.

Construction oversampling must be set from observed pilot attrition before generation. It may not be increased after detector results are observed.

## Manipulation acceptance

Before final generation, two detector-blinded reviewers independently evaluate the pilot. Recommended freeze criteria:

- semantic intent preserved: >= 95% of variants;
- requested action preserved: >= 95%;
- entity/channel/safety preservation: >= 98%;
- for C3 and C6, less-direct-than-C2 judgment: >= 80% among otherwise valid paired items;
- categorical reviewer agreement: Cohen's kappa >= 0.70 on core validity fields, or documented adjudication if lower.

These thresholds are preregistered research decisions for this project version and must not be changed after detector outcomes are inspected.

## Human review

The pilot and final benchmark require human review. AI-generated or automatically produced review decisions do not count as human review. Confirmatory detector evaluation is blocked until the final review state is complete.
