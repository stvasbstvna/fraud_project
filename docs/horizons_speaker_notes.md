# HORIZONS speaker notes

## Slide 1 — Research question (0:00–0:55)
Smishing is fraudulent SMS designed to induce an unsafe action. Ask whether detectors respond to the underlying intent or to familiar surface wording. Do not promise that the study will prove detector failure.

## Slide 2 — Paired design (0:55–2:00)
Each original and rewrite shares a pair ID and label. The comparison is within-message, reducing variation unrelated to wording.

## Slide 3 — Frozen safeguards (2:00–3:05)
Models and splits are frozen. Generation receives no detector scores or feedback. URLs remain defanged. No model was fit during evaluation.

## Slide 4 — Current workflow state (3:05–4:00)
There are 156 original pairs. 153 rewrites passed automated checks; 3 were rejected. Human semantic review approved 153 rows, with 0 pending. The reported v1 evaluation now uses the complete approved set.

## Slide 5 — Recall and F1 (4:00–5:20)
LR recall moved 98.6% to 97.9%; RF moved 97.9% to 97.2%. F1 moved 96.9% to 96.2% and 95.6% to 95.2%. Each model gained one additional miss; avoid saying detectors broadly failed.

## Slide 6 — Paired inference (5:20–6:25)
The discordant transition is one detected-to-missed and zero missed-to-detected phishing cases for each model. Exact McNemar p is 1.0. Say explicitly: this sample does not establish a significant paired classification change.

## Slide 7 — Confidence (6:25–7:35)
The metric is original probability minus rewrite probability. Its mean is slightly negative for both models, so confidence increased slightly on average. Both bootstrap intervals cross zero. Probability movement is sensitivity; crossing the frozen threshold is classification failure.

## Slide 8 — Legitimate controls (7:35–8:40)
Specificity is poor, especially for random forest, but only ten legitimate controls exist. Present this as a separate generalization/false-positive limitation and emphasize uncertainty from the small denominator.

## Slide 9 — Benchmark v2 (8:40–10:20)
The pilot validates schemas and review logic only. Final v2 needs authorized anchors, frozen prompts, a versioned generator pool, human approval of complete condition sets, provenance enforcement, and detector-blinded generation.

## Slide 10 — Close (10:20–12:00)
The contribution today is a reproducible paired robustness workflow and a disciplined null/inconclusive result. Human review is complete for v1; broader detector claims still require preregistered confirmatory v2 testing.
