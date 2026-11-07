# Research Question

Which linguistic changes cause detector behavior to change when malicious intent remains fixed?

## Dataset

The new canonical construction contains 441 unique synthetic candidate texts (254 phishing-labelled, 187 legitimate-labelled). Labels and intent are not yet validated. There are 3,087 planned C0–C6 slots, 441 populated C0 texts, zero generated rewrites and zero frozen rows. Do not describe this as 3,087 completed messages. The older 48-row pilot has only 36 unique texts.

## Experimental Conditions

C0 original safe baseline; C1 light lexical change; C2 direct action; C3 same action expressed indirectly; C4 natural normalization; C5 strong paraphrase; C6 high-distance meaning-preserving rewrite. These are planned controlled transformations, not observed experimental findings.

## Models

Existing frozen TF-IDF + Logistic Regression and TF-IDF + Random Forest; unchanged SHA-256 verified. Each fitted vocabulary has 3,715 features; default decision threshold 0.5. No v2.1 predictions have been run.

## Main Result

New v2.1 empirical result: NOT AVAILABLE. The audit found duplicate source templates and unresolved intent labels, which must be corrected before confirmatory claims.

Prior v1 only: 143 phishing pairs; recall changes LR 98.6014%→97.9021%, RF 97.9021%→97.2028%; one net additional miss per model, exact McNemar p=1.0. This small observed change does not establish systematic detector degradation.

## Strongest Example

No eligible v2.1 representative example exists. A prior illustrative UNIONBANK example (`BRW-0099`) has LR 0.5653773212→0.4898664850 at threshold 0.5, detected→missed. Report it as historical illustration, not the largest/representative v2.1 effect. Exact wording differences remain in the preserved v1 paired file; no new rewrite is invented here. A future representative v2.1 frame is selected nearest the median frame-average absolute score change, ties by stable ID, after full reporting.

## False Positive Example

No independently verified v2.1 legitimate example is available. Prior banking baseline aggregate: 7/10 LR controls and 10/10 RF controls were false positives. Small sample; no claim that vocabulary caused these errors. An example requires independent legitimate-label verification, safe text and exact saved probability before presentation.

## Graph Explanations

These five graphs are planned; no new empirical graph is currently available:

1. Recall: X lists C0–C6; Y is the fraction of phishing frames detected, from 0 to 1. Lines identify LR/RF. It will show whether reviewed conditions change detection rates.
2. Score change: X lists C1–C6; Y is baseline probability minus rewrite probability. Points/intervals show model-specific paired means and frame-bootstrap uncertainty. Positive values mean lower rewrite scores.
3. Distance versus score change: X measures surface-text difference; Y measures score change. Each point is one rewrite for one detector. Association is not proof of lexical causality.
4. Transitions: X lists conditions; rows list the four decision-change directions; cell color/count shows how many frames changed, separately per model. Both new errors and recoveries matter.
5. Message trajectory: X lists C0–C6; Y is probability 0–1 for one prospectively selected representative frame. LR/RF lines and threshold 0.5 explain how decisions arise. This frame must not be selected solely for dramatic change.

## Safe and unsafe claims

Safe now: explain research question, controlled design, audit findings and explicitly historical v1 observations. Do not claim new rewrite effectiveness, distance-response significance, approved labels, 8,750 completed rows, completed human validation, or general detector vulnerability.
