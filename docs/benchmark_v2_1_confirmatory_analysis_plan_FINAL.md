# Benchmark v2.1 preregistered dose-response confirmatory analysis plan

## Primary scientific question

Does progressively stronger semantic-preserving linguistic transformation systematically change frozen TF–IDF banking-smishing detector behavior while intent, requested action, entity, channel, destination, label, scenario meaning, and safety state remain fixed?

The primary population is phishing-labelled, human-approved, complete C0–C6 frame sets. Legitimate controls form a separate specificity/FPR analysis and are not mixed into the phishing primary endpoint.

## Analysis representation

`combined_surface_distance` is computed from text alone before detector outputs are read. Phishing probabilities are clipped to `[1e-6, 1-1e-6]` and transformed with the logit to avoid fitting a linear model directly to a bounded outcome. For each detector and frame, within-frame logit probability is regressed on measured distance; inference is performed on one slope per frame, preserving the frame as the independent unit. Binary false-negative slopes are calculated analogously from the condition-level miss indicator. Detector-average slopes test the common response; paired LR-minus-RF frame slopes test detector interaction.

Every primary and secondary-confirmatory test is two-sided. Expected deterioration may guide presentation but does not convert the inferential tests to one-sided tests.

## Confirmatory hypotheses

| ID | Tier | Scientific question / conditions | Endpoint | Unit and test | Effect size |
|---|---|---|---|---|---|
| H1_CONTINUOUS_DISTANCE_TREND | PRIMARY | Does confidence change systematically with measured surface distance? | clipped logit phishing probability | frame-level detector-mean distance slope; one-sample t test across frames | mean logit-probability slope per unit distance |
| H2_BINARY_FN_DISTANCE_TREND | PRIMARY | Does false-negative behavior change systematically with distance? | false-negative indicator | frame-level detector-mean distance slope; one-sample t test | mean FN slope per unit distance |
| H5_C0_VS_C1_MINIMAL_LEXICAL | SECONDARY CONFIRMATORY | Is light lexical variation distinct from anchor? | clipped logit probability | paired frame contrast, averaged across detectors | C1−C0 |
| H6_C2_VS_C3_ACTION_EXPLICITNESS | SECONDARY CONFIRMATORY | Does softened expression of the same action differ from direct wording? | clipped logit probability | paired frame contrast, averaged across detectors | C3−C2 |
| H7_C0_VS_C4_NATURALIZATION | SECONDARY CONFIRMATORY | Does natural-language normalization differ from anchor? | clipped logit probability | paired frame contrast, averaged across detectors | C4−C0 |
| H8_C0_VS_C5_STRONG_PARAPHRASE | SECONDARY CONFIRMATORY | Does strong semantic-preserving paraphrase differ from anchor? | clipped logit probability | paired frame contrast, averaged across detectors | C5−C0 |
| H9_C0_VS_C6_COMBINED_HIGH_DISTANCE | SECONDARY CONFIRMATORY | Does the combined high-distance condition differ from anchor? | clipped logit probability | paired frame contrast, averaged across detectors | C6−C0 |

The five contrasts are nonredundant manipulation interpretations: minimal lexical change, isolated action explicitness, conversational normalization, strong paraphrase, and combined maximum-distance transformation. The twelve patch pairwise detector tests are not primary.

## Multiplicity

Exactly seven new dose-response p-values form one Holm family at FWER 0.05: two trend hypotheses and five pooled condition contrasts. This is not the old seven-test H1–H4 family. Sort raw p-values ascending. Compare the smallest with `0.05/7`, the next with `0.05/6`, continuing step-down until the first failure; all later hypotheses are not rejected. Report raw and Holm-adjusted p-values for every member. Descriptive recall, FNR, transition counts, condition medians, component distances, individual-detector condition contrasts, and the two detector-by-distance interactions do not add confirmatory tests.

## Supporting and exploratory analysis

Report recall/FNR and paired transitions by condition, mean/median probability shifts, alternative distance components, nonlinear trends, error analysis, condition results per detector, and continuous/binary detector-by-distance interactions as prespecified exploratory/supporting estimates with confidence intervals. Interactions remain relevant model-comparison outputs but are not powered as additional confirmatory claims. Legitimate specificity/FPR and condition sensitivity are reported separately. No exploratory result is relabeled confirmatory.

## Missingness and clustering

Confirmatory analysis requires complete approved C0–C6 sets for both detectors. No imputation. Available-pair results are sensitivity only. Bootstrap or resampling, where used, samples `frame_id` and retains every condition and both detectors together.

## Interpretation

Rejection indicates evidence of the specified association/contrast under the frozen construction and review rules, not universal detector vulnerability or lexical causality. Failure to reject is a valid null result. Manipulation validity and semantic preservation are prerequisites for confirmatory interpretation.
