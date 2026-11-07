# Controlled linguistic rewriting methodology

Research question: Which linguistic changes cause detector behavior to change when malicious intent remains fixed? The operational estimand is paired detector response under reviewed linguistic transformations; broad claims of lexical causality require stronger manipulation isolation than this design alone supplies.

## Units, populations and controls

Independent unit: source frame, with C0–C6 repeated observations and both frozen detectors. Primary population: English banking SMS with reviewed intent/action/label, verified provenance/license and no training/template overlap. 750 phishing and 500 legitimate frames are targets, not achieved samples. Existing synthetic anchors are candidates with unresolved intent validity; templated duplicates cannot inflate N. C0 is the unchanged safe/defanged source; historical original raw text is retained separately. Defanging is common to all conditions, so claims concern the defanged baseline.

Across conditions keep true label, malicious/legitimate intent, action, literal entity, destination, channel, language, factual scenario and safety fixed. C2/C3 compare directness of the same action. Generation is blinded to all detector information; human validation occurs before scores. Two independent manual reviews check each available source/variant; objective checks are never semantic approval. Pilot manipulation review and attrition rules precede full generation/freeze.

## Measurements

Jaccard uses lowercase alphanumeric/underscore token sets; empty/empty=1. Normalized edit distance is character Levenshtein / max character length (both empty=0). For LR and RF separately, use **existing fitted** L2-normalized vectorizers to compute cosine similarity without fitting. Identical strings have similarity 1 even if both map to zero vectors; nonidentical zero-overlap vectors have similarity 0. Record the two similarities, with their arithmetic mean as `tfidf_cosine_similarity`.

`surface_distance = ((1 − jaccard_similarity) + normalized_edit_distance + (1 − mean_frozen_cosine_similarity)) / 3`.

Equal fixed weights place three bounded surface-change summaries on a transparent 0–1 scale; they are not independent constructs or validated semantic metrics. Version `frozen-vectorizer-equal-weight-v1`. Weights are not optimized against outcomes. The earlier corpus-refitted distance definition remains archived and cannot be mixed silently with this representation. Compute distance before any new detector scoring; assess C1<C5/C6 manipulation on the prespecified pilot, not by filtering on detector outcomes. Current frozen vectorizers happen to match, so their mean does not add independent information.

## Outcomes

Report accuracy, precision, recall, F1, TN/FP/FN/TP, FNR=FN/(FN+TP), FPR=FP/(FP+TN), mean/median phishing probability. Undefined denominators stay missing. `confidence_drop=P(C0)−P(Ci)`; positive is a lower score after rewriting. Distinguish detected→missed, missed→detected, legitimate→false-positive, false-positive→legitimate. Report all frames in statistics; rank absolute changes only in descriptive example tables. Threshold remains 0.5 with original pipeline tie behavior.

## Stage gates

Registry/source audit → unique pending frames → source semantic review → eligible pilot request manifest → external structured generation → objective safety/schema validation → blinded independent reviews → distance/directness/preservation manipulation validation and frozen attrition rule → complete reviewed matrix freeze/hash → frozen-model evaluation → paired analysis → tables/figures. Source and generation readiness are distinct from final freeze readiness; a missing output cannot be used as a prerequisite for its own creation. Existing old file-existence checks are not reused as final approval.
