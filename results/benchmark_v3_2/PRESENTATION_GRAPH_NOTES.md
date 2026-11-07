# Presentation graph notes

Read each note alongside its graph and exact-data CSV. Allow approximately 20–40 seconds per figure.

## Source and cohort flow (20–40 seconds)

How many records reach each cohort stage? Existing raw records rescanned: 67380; New expanded lexical hits: 707; Rights-cleared unique candidate pool read: 12954; Fitting-family-compatible source packet: 1065; English/financial machine approved: 16; Policy-eligible robustness C0: 12; Initial generation jobs: 48; Generated attempts: 89; Approved rewrite pairs: 14; Complete trajectories: 0 Counts describe cohort selection; consult stage units. Selection counts do not establish population prevalence.

## Condition completeness (20–40 seconds)

Which conditions are available and included in the paired cohort? 0 frames are retained in every condition. Generated/approved/rejected counts deduplicate retries; rejected means no approved attempt for that slot. Availability and attempts are separate quantities; attempt_count and retry_count are exported separately. C0 has no generated slots. A missing condition is never a zero detector score.

## Recall by condition (20–40 seconds)

How does recall vary by model and condition? No primary complete frames; estimates are unavailable. Denominators are explicitly shown for true_label=1; undefined rates remain missing. Rates compare the same complete frames within each true-label stratum. These rates do not estimate deployment prevalence or causal effects.

## False positive rate by condition (20–40 seconds)

How does false positive rate vary by model and condition? No primary complete frames; estimates are unavailable. Denominators are explicitly shown for true_label=0; undefined rates remain missing. Rates compare the same complete frames within each true-label stratum. These rates do not estimate deployment prevalence or causal effects.

## Signed phishing-probability movement (P0 − Pi) (20–40 seconds)

How large is paired movement relative to C0 within each true class? No primary complete frames; estimates are unavailable. Legitimate and phishing observations are labelled separately; a class with N=0 has no estimate. Positive signed movement means lower phishing probability than C0. Intervals resample frames with seed 42. This describes paired score sensitivity within each class for retained frames. Probability movement alone does not establish evasion, correctness, or semantic equivalence.

## Absolute phishing-probability movement |P0 − Pi| (20–40 seconds)

How large is paired movement relative to C0 within each true class? No primary complete frames; estimates are unavailable. Legitimate and phishing observations are labelled separately; a class with N=0 has no estimate. Positive signed movement means lower phishing probability than C0. Intervals resample frames with seed 42. This describes paired score sensitivity within each class for retained frames. Probability movement alone does not establish evasion, correctness, or semantic equivalence.

## Surface distance versus score movement (available pairs; exploratory) (20–40 seconds)

Do larger surface changes accompany larger score changes? 42 model-variant observations have surface distance; missing distances are omitted from marks. The plot describes association, with repeated observations belonging to frames. When the primary cohort is empty, these are explicitly exploratory available-pair observations. Association is not causation; surface distance is not semantic distance. Available-pair observations are not complete-cohort inference.

## Four threshold-transition types (20–40 seconds)

Which paired predictions cross the detector threshold? No primary complete frames; estimates are unavailable. Four class-specific crossings are counted: detected→missed and missed→detected for phishing; legitimate→false-positive and false-positive→legitimate for legitimate messages. Unchanged predictions are excluded. N is the class denominator; eligible_N is the baseline state at risk of each crossing; absent-class rates remain unavailable. Do not combine phishing misses and legitimate false positives as a single evasion measure.

## Representative complete frame (nearest median mean absolute movement): unavailable (20–40 seconds)

Is a paired frame available to illustrate? No primary complete frames; estimates are unavailable. No eligible nonbaseline pair is available for example selection. An unavailable example must remain unavailable. Do not substitute a frame outside the stated selection cohort.

## EXTREME CASE—NOT REPRESENTATIVE (20–40 seconds)

What does a concrete paired frame look like? Strongest single pair among all approved available pairs: frame nus-5294, ModernBERT, C5, |Δ|=0.0613; frame complete-case membership=False. EXTREME CASE—NOT REPRESENTATIVE. This illustrates the stated selection rule; exact before/after text, model probabilities, true labels, and the frozen threshold are exported. A single frame cannot establish overall model performance or population effects.

## Manipulation-check distance distributions (20–40 seconds)

How much surface variation did each condition produce? Distributions retain each metric's definition; unavailable values are omitted and observed N is exported. TF-IDF cosine is lexical feature similarity; Jaccard and edit measures describe surface changes. Lexical cosine similarity must not be described as semantic preservation.

## Semantic preservation versus surface distance (20–40 seconds)

Were meanings preserved across the observed surface changes? Semantic similarity scores are unavailable. This plot uses reviewed preservation decisions as a binary outcome, without inventing semantic scores. Reviewed binary decisions and recorded similarity scores are distinct evidence types. Neither lexical cosine nor missing semantic scores are evidence of semantic equivalence.
