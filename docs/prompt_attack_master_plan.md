# Prompt-Based Robustness Research Plan

## 1. Executive Summary

This project now studies whether controlled prompt-based rewrites reduce a phishing detector's ability to recognize confirmed banking phishing. The existing TF-IDF + Logistic Regression model remains a useful baseline, but its 97.7% unified-test accuracy and 97.0% confirmed-banking-pilot accuracy do not establish robustness. The current test data may share vocabulary, source artifacts, and formatting with the training data.

The next contribution is a paired, banking-focused robustness benchmark. Start with 30-50 confirmed banking phishing messages that the baseline detects correctly, create or obtain safe intent-preserving variants under prompt IDs P0-P7, run the unchanged detector, and measure probability drop, false-negative rate (FNR), and Attack Success Rate (ASR). All generated text must remain defanged and placeholder-based. Licensed public data may be redistributed; unclear-license data must remain analysis-only.

## 2. Updated Research Direction

- Previous stage: built a unified 11,186-message pipeline, filtered 6,372 banking candidates, trained a baseline, and manually reviewed a 225-row pilot.
- Problem: very high test accuracy can indicate an easy or source-dependent split rather than robust understanding of phishing intent.
- New stage: evaluate the same confirmed banking-phishing intent before and after controlled prompt-based transformations.
- Main question: **How does prompt-based adversarial rewriting affect phishing-detector robustness on confirmed banking-related phishing messages?**
- Practical value: the study identifies which wording/channel transformations cause missed phishing and which mitigations recover recall.
- Baseline role: TF-IDF is old, but that is exactly why it is useful as a baseline. The contribution is not the model itself. The contribution is the banking-focused prompt-based robustness evaluation.
- Primary evidence: paired tables by prompt ID, with before/after probabilities, recall, FNR, and ASR.

## 3. Research Paper Groups

- **A - LLM-generated phishing/smishing:** generation, authorship comparisons, public variant datasets, and SMS detection.
- **B - Prompt robustness/evaluation:** systematic prompt taxonomies and evaluation protocols. These works mostly evaluate prompts given to LLMs; they are methodological inspiration, not direct phishing-detector attacks.
- **C - Adversarial text attacks:** semantic, contextual, lexical, and character perturbations against classifiers.
- **D - Detection/mitigation:** phishing detection, calibration, adversarial preprocessing/training, external-context features, and human-facing explanations.

## 4. Detailed Literature Table

| Paper/resource | Year | Group | Data used | Prompt/generation method | Models/methods | Metrics | Main result | Already done | Gap for this project | Planned use |
|---|---:|:---:|---|---|---|---|---|---|---|---|
| [Francia et al., TRAPD](https://arxiv.org/abs/2406.13049) | 2024 | A | Personalized SMS for consenting participants; 25 targets reported in the abstract | GPT-4 and human authors used participant attributes; prompts were used, but the full reusable prompt set is not established in the abstract | Ranked-order human study, permutation/logistic analyses | Rank, click likelihood, authorship judgments | AI messages were often perceived as convincing; results were a small human-perception pilot, not detector evasion | AI-vs-human personalized smishing | No paired banking detector evaluation | Motivate SMS-style P1 and authorship caveats; only safe paraphrased prompt structure |
| [Toth et al., PhishFuzzer](https://arxiv.org/abs/2511.21448) / [repository](https://github.com/DataPhish/PhishFuzzer) | 2026 version | A | 3,300 seed emails plus 19,800 variants (23,100 total) | Six variants per seed across entity type and length; scripts and prompt files are public | Qwen-2.5-72B and Gemini-3.1-Pro classification | Accuracy, macro/F1, template success and consistency/failure metrics | Shows template-linked variant evaluation and metadata effects | Seed-linked LLM rephrasing benchmark | Not banking-specific; explicit repo/data license is not visible | P7 design and template-family metrics; analysis-only until licensing is resolved |
| [Gutierrez et al., Cross-model evaluation](https://www.frontiersin.org/journals/big-data/articles/10.3389/fdata.2026.1883452/full) | 2026 | A/D | 5,000 human and 4,986 generated phishing emails | Generated phishing across GPT-4.1, DeepSeek 3.2, and Llama 3.3 70B; not paired rewrites of the human corpus | 17 stylometric features, LR/XGBoost, threshold recalibration | F1, cross-model gap, feature importance | Cross-generator gap fell substantially after target-model threshold recalibration | Human-vs-LLM authorship and calibration | Does not isolate same-message banking rewrites | Existing P6 condition and calibration mitigation |
| [Wang et al., SmishX](https://www.usenix.org/conference/soups2025/presentation/wang) / [code](https://github.com/yizhu-joy/SmishX) | 2025 | A/D | Relabeled real-world SMS data and user study (N=175) | LLM agents extract context, collect evidence, reason, and summarize an explanation; detection prompts, not attack-generation prompts | GPT-4o primary; local-model checks; contextual retrieval | Accuracy, user detection, SUS | 98.8% overall accuracy reported; explanations improved user decisions; SUS 82.6 | Explainable SMS phishing detection | No prompt-rewrite attack benchmark | SMS/channel features, explanation and mitigation design |
| SmishTank (Timko and Rahman; [paper](https://arxiv.org/abs/2402.18430)) | 2024 | A | Community-reported smishing snapshot | No LLM prompt method | Dataset construction | Counts/descriptive statistics | Provides real-world smishing provenance | Human-reported SMS source | Stable export and redistribution permission remain unclear | Candidate source only after access/license verification |
| [PromptBench library](https://arxiv.org/abs/2312.07910) | 2023/24 | B | General NLP/LLM benchmarks | Prompt construction, engineering, adversarial prompt attack, dynamic and semantic evaluation | Unified evaluation library | Task metrics, robustness/transfer analyses | Organizes prompt methods and attacks systematically | Prompt taxonomy/evaluation infrastructure | Attacks prompts to LLMs, not phishing messages to a classical detector | Justify fixed prompt IDs, versions, and comparable conditions |
| [PromptBench robustness benchmark](https://arxiv.org/abs/2306.04528) | 2023 | B | Multiple LLM tasks/datasets | Character-, word-, sentence-, and semantic-level perturbations to prompts | LLM robustness benchmark | Performance degradation/robustness | Demonstrates multi-level prompt perturbation evaluation | Systematic prompt perturbation | Different target and task | Inspiration for P3-P4 taxonomy and degradation reporting |
| [PromptAttack](https://openreview.net/forum?id=VVgGbB9TNV) | 2024 | B | AdvGLUE-style tasks | Prompt-based adversarial example generation | LLM-driven attack and adversarial training | Attack performance and robustness | Provides prompt-based adversarial-data methodology | Prompt-generated adversarial examples | Not phishing/banking and not safety-defanged | Methodological inspiration; do not copy operational generation instructions |
| [TextFooler](https://arxiv.org/abs/1907.11932) | 2020 | C | Text classification and entailment datasets | Importance-ranked synonym substitution with semantic/grammar constraints; no LLM prompt | Black-box attack against BERT/CNN/RNN | Attack success, perturbation, human validity | Strong semantic-preserving word-level attack | Classifier-focused semantic attack | Not phishing-specific; synonym changes may alter intent | P3 semantic-preserving rewrite constraints |
| [BAE](https://aclanthology.org/2020.emnlp-main.498/) | 2020 | C | Standard text-classification datasets | BERT masked-LM insertion/replacement; no prompt method | Black-box contextual attack | Attack strength, grammaticality, semantic coherence | Contextual replacements improve naturalness over simple synonyms | Contextual token attack | Not channel-aware or phishing-specific | P3/P4 contextual perturbation inspiration |
| [BERT-Attack](https://arxiv.org/abs/2004.09984) | 2020 | C | Standard classification tasks | BERT masked-LM candidates; no LLM prompt | Word-importance and contextual replacement | Success rate, perturbation percentage, fluency | Effective semantically preserved attacks | Contextual word attack | Not banking/phishing | P3 design and semantic checks |
| [TextBugger](https://arxiv.org/abs/1812.05271) | 2018 | C | Sentiment/toxicity services and datasets | Word- and character-level perturbations; no LLM prompt | Black/white-box attacks | ASR, semantic similarity, time | Demonstrates classifier vulnerability to small surface changes | Lexical/character attack | Some perturbations are unrealistic for SMS | P4 lexical/character baseline with readability constraints |
| [DeepWordBug](https://arxiv.org/abs/1801.04354) | 2018 | C | Eight datasets including spam detection | Critical-token scoring plus character edits; no LLM prompt | Black-box character attack | Accuracy drop, edit distance | Small edits can sharply reduce model accuracy | Character-level black-box attack | Does not preserve phishing-specific semantics automatically | Conservative P4 baseline |
| [TextAttack](https://aclanthology.org/2020.emnlp-demos.16/) | 2020 | C/D | Framework across common NLP datasets/models | Goal + constraints + transformation + search | 16 attack recipes, augmentation, adversarial training | Recipe-specific task/attack metrics | Makes attacks and defenses reproducible | Reproducible attack/augmentation framework | No banking benchmark out of the box | Optional implementation and mitigation framework |
| [Next-Generation Phishing](https://arxiv.org/abs/2411.13874) | 2024 | A/D | Traditional and LLM-rephrased phishing emails | LLM rephrasing; prompt details must be checked in the paper before reuse | Commercial filters and classical ML detectors | Detection performance | Reports detector weakness under LLM-rephrased phishing | Direct rephrased-phishing evaluation | Banking/SMS pairing and safe prompt taxonomy remain open | Closest detector-evasion comparison; verify protocol before citing numeric claims |

Status language used above is deliberate: “prompts used” does not mean the full prompt is published; “LLM generation” does not imply paired rewriting; adversarial-text papers are methodological inspiration rather than phishing-prompt sources.

## 5. What Others Already Did

**Already done:** human-vs-AI phishing/smishing comparisons; GPT-4 personalized smishing generation; human persuasiveness/click-likelihood studies; LLM phishing-email corpora; systematic prompt robustness frameworks; semantic/contextual/character adversarial text attacks; explainable SMS-phishing detection; cross-generator calibration.

**Not fully covered in this exact angle:** a confirmed-banking, paired prompt-rewrite attack against one frozen detector; prompt-ID comparison across style/channel/semantic/lexical conditions; ASR restricted to originally correct banking-phishing inputs; human-written, LLM-generated, and SMS banking messages in one provenance-aware pipeline; safe placeholder-only transformations; detector degradation and mitigation by prompt type.

## 6. What My Project Adds

| Contribution | What I do | Why useful | Builds on | Proof table/result |
|---|---|---|---|---|
| Banking-focused prompt benchmark | Restrict evaluation to manually confirmed financial-account phishing | Removes topic noise from keyword-only filtering | SmishX, SmishTank, phishing corpora | Dataset construction table |
| Confirmed base set | Select 30-50 originally correct phishing rows from the 91-row pilot | Makes ASR causally interpretable | Existing pilot | Base-set audit table |
| Research-based prompt taxonomy | Version P0-P7 with fixed, safe transformation goals | Makes variants reproducible and comparable | PromptBench, TextFooler, BAE, PhishFuzzer | Prompt taxonomy table |
| Paired degradation analysis | Compare each sample before/after under the same frozen detector | Controls for original intent and sample identity | Adversarial-text evaluation | Prompt result table |
| Banking ASR | Count originally detected samples that flip to non-phishing | Directly measures evasion under each condition | Text attack literature | ASR table with confidence intervals |
| Safety-aware methodology | Keep placeholders, defang destinations, remove operational details, review intent | Enables defensive study without producing deployable scams | Responsible data handling | Safety/intent verification counts |
| Mitigation evaluation | Test augmentation, SMS/intent/action features, thresholds, quarantine | Turns vulnerabilities into defensive recommendations | TextAttack, SmishX, calibration work | Mitigation table |

## 7. Prompt-Based Attack Definition

**Prompt-Based Adversarial Rewriting Attack:** a controlled prompt-based transformation that changes wording, tone, format, or surface structure while preserving the same high-level phishing intent and true label. It tests whether a detector relies on surface patterns instead of robust phishing intent.

Safety constraint: generated or rewritten examples must be defanged and placeholder-based, or taken from public/approved research data. The experiment must not create operational phishing content, working destinations, real impersonation, real contact details, or usable credential/payment instructions.

## 8. Prompt Taxonomy

Safe abstract template: `Given a defanged banking-scam summary containing placeholders, create a non-operational variant that preserves the high-level intent label but changes [style/length/wording/channel format]. Keep every placeholder. Do not add real destinations, identities, contact details, credential requests, payment instructions, or usable attack steps.`

| ID | Name | Inspiration | Change | Input -> output | Safety restriction | Expected weakness | Metrics |
|---|---|---|---|---|---|---|---|
| P0 | Original | Control condition | None | Approved base text -> identical text | Defang before storage if needed | None/control | Recall, FNR, probability |
| P1 | SMS-style | TRAPD; SmishX | Shorter, conversational, SMS formatting | Defanged email/SMS summary -> SMS-like variant | Placeholders only; no targeting | Channel/length shift | ASR, probability drop, SMS-stratified FNR |
| P2 | Formal notification | Phishing-generation literature | Formal tone and structure | Safe summary -> formal notice | No real institution/brand | Removal of informal scam cues | ASR, probability drop |
| P3 | Semantic-preserving rewrite | TextFooler, BAE, BERT-Attack | Vocabulary and syntax | Safe summary -> meaning-equivalent variant | Reviewer verifies same intent | TF-IDF lexical dependence | ASR, similarity, probability drop |
| P4 | Lexical/character perturbation | TextBugger, DeepWordBug, PromptBench | Small readable lexical/character changes | Defanged text -> constrained perturbation | Do not alter placeholders/label; readability threshold | Tokenization sensitivity | ASR, edit rate, probability drop |
| P5 | Defanged intent-preserving | Existing 30-pair pilot | Replace operational entities/actions with placeholders | Original -> placeholder variant | Mandatory defanging | Reliance on brands, URLs, direct requests | Existing 30-row paired results |
| P6 | Existing public LLM-generated | Cross-model corpus | Independent LLM-authored messages | Public approved data -> comparison set | Preserve supplied sanitization | Authorship/source shift | Unpaired recall/FNR; not paired ASR unless linked |
| P7 | PhishFuzzer-style seed variant | PhishFuzzer | Entity-type and length-controlled seed variants | Approved seed -> linked variants | Use only licensed/authorized data; safe placeholders | Entity and length sensitivity | Template success, ASR, probability drop |

## 9. Dataset Plan

Four machine-readable files plus one readable view are defined in `data/prompt_attack/`.

1. `source_pool.csv`: one row per source, including access, license, analysis, redistribution, citation, and notes.
2. `base_banking_phishing_set.csv`: 30-50 selected rows from `confirmed_banking_phishing_only.csv`, restricted to true phishing, banking-related, and correctly predicted by the baseline. Target balance: 15 human, 10 LLM-generated, and 5-10 SMS; use all eligible SMS if fewer exist.
3. `prompt_attack_variants.csv`: one-to-many link from each base sample to P0-P7 variants, with prompt source and safety/intent-review fields.
4. `prompt_attack_evaluation_results.csv`: frozen-model before/after predictions, probabilities, flip indicator, probability drop, ASR, model/version, and run date.
5. `prompt_attack_readable_sample.csv`: short defanged summaries for professor/paper inspection.

The prompt describes a 91-row confirmed pilot, but that source CSV is not currently in this repository. The four experiment files therefore contain schemas only; no research rows are fabricated. Place the reviewed file at `data/analysis_only/confirmed_banking_phishing_only.csv` or adapt the build step to its actual safe local path.

## 10. Filtering Rules

- Banking-related = yes only when manual review confirms bank account, card, payment/transfer, suspicious activity, login verification, fraud/security alert, financial app/service, or financial-brand imitation.
- Banking-related = no when the main topic is parcel delivery, casino, job/income, health, cloud storage, HR benefits, generic app login, carrier service, social media, or unrelated promotion.
- Keyword matches remain candidates, not final banking labels.
- True phishing uses the corrected true label. A legitimate banking message is never counted as a false negative.
- Attack inputs must have `true_label=phishing`, `banking_related=yes`, and `baseline_prediction=phishing`.
- Authorship remains unknown unless source provenance supports human, generated, or rewritten.
- Near-duplicate families and all variants of one sample stay in the same split.
- Intent preservation and removal of operational details require human verification before evaluation.

## 11. Experiment Design

| Stage | Input | Procedure | Output |
|---|---|---|---|
| 1. Baseline | Unified split | TF-IDF + Logistic Regression; freeze preprocessing, vocabulary, and threshold | Baseline metrics and model artifact |
| 2. Confirmed subset | 91 reviewed phishing rows | Apply strict banking/label rules and select 30-50 originally correct rows | Base set |
| 3. Variants | Base set | Apply P0-P7 where permitted; retain placeholders; log prompt/model/version/seed | Variant table |
| 4. Re-test | Frozen baseline + variants | Predict once under the frozen pipeline | Row-level results |
| 5. Analyze | Row results | Aggregate overall, by prompt, channel, authorship, and source; bootstrap by sample | Main results/ASR tables |
| 6. Mitigate | Training-split variants only | Augmentation, SMS features, intent/action features, threshold calibration, confidence-tiered quarantine | Matched mitigation comparison |

Pre-register the primary set and prompt conditions. P6 is an unpaired authorship/source-shift comparison unless the source provides seed links. P5's existing 30-row result is a pilot and should not be mixed with the new selected base set unless selection and provenance match.

## 12. Metrics

- Accuracy, precision, recall, F1, FNR, false-positive rate, and average phishing probability.
- `probability_drop = probability_before - probability_after`.
- `became_false_negative = 1` only if the original was correctly predicted phishing and the variant is predicted non-phishing.
- `ASR = successful flips / originally detected phishing inputs` for each prompt condition.
- Report numerator, denominator, and a 95% confidence interval clustered/bootstrapped by `sample_id`.
- Report semantic/intent-review pass rate, edit rate for P4, and rejection count for safety/label drift.
- Do not calculate precision/accuracy from a phishing-only attack subset without clearly stating that the subset contains no negatives; recall/FNR/ASR are the main measures there.

## 13. Required Tables

| # | Title | Columns | Example row | Use |
|---:|---|---|---|---|
| 1 | Literature comparison | Work, year, group, data, prompt status, method, metrics, result, gap, use | TextFooler; 2020; C; semantic substitutions; no prompt | Both |
| 2 | Research gap | Prior capability, existing evidence, missing element, project response | LLM phishing exists; not paired banking rewrites; paired benchmark | Both |
| 3 | Contributions | Contribution, action, novelty/use, prior work, proof | Banking ASR; flips on confirmed inputs; ASR table | Both |
| 4 | Dataset sources | Source, channel, rows, authorship, license, analysis, redistribution | SmishX; SMS; 1,200; unknown; MIT repo | Both |
| 5 | Dataset construction | Step, input rows, exclusions, output rows, reason | Manual banking confirmation; 225 -> 100 | Both |
| 6 | Prompt taxonomy | ID, type, source, change, safety, weakness, metrics | P1; SMS-style; TRAPD/SmishX | Both |
| 7 | Attack design | Stage, input, procedure, output, control | Frozen baseline -> variants | Slides |
| 8 | Prompt attack results | ID, rows, before/after detection, recall/FNR, probabilities, ASR | P5 values below | Both |
| 9 | Attack success | ID, eligible, flips, ASR, CI, failed safety/intent review | P3; TBD | Both |
| 10 | Mitigation | Mitigation, training change, test set, recall/FNR/ASR before/after, cost | Variant augmentation; TBD | Both |

Prompt attack result template:

| Prompt ID | Rewrite type | Rows | Detected before | Detected after | Recall before | Recall after | FNR after | Avg probability before | Avg probability after | Probability drop | ASR |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| P0 | Original | TBD | TBD | TBD | TBD | TBD | TBD | TBD | TBD | TBD | - |
| P1 | SMS-style | TBD | TBD | TBD | TBD | TBD | TBD | TBD | TBD | TBD | TBD |
| P2 | Formal notification | TBD | TBD | TBD | TBD | TBD | TBD | TBD | TBD | TBD | TBD |
| P3 | Semantic rewrite | TBD | TBD | TBD | TBD | TBD | TBD | TBD | TBD | TBD | TBD |
| P4 | Lexical perturbation | TBD | TBD | TBD | TBD | TBD | TBD | TBD | TBD | TBD | TBD |
| P5 | Defanged pilot | 30 | 28 | 30 | 93.33% | 100.00% | 0.00% | 0.8484 | 0.8507 | -0.0023 | 0.00% |
| P6 | Existing LLM-generated | TBD | TBD | TBD | TBD | TBD | TBD | TBD | TBD | TBD | N/A if unpaired |
| P7 | PhishFuzzer-style | TBD | TBD | TBD | TBD | TBD | TBD | TBD | TBD | TBD | TBD |

## 14. Slide Content

1. **Updated direction after meeting**
   - Previous: text/URL features for banking smishing.
   - Current: controlled prompt-based variants of confirmed banking phishing.
   - Question: how much does a frozen detector degrade?
2. **Why TF-IDF first**
   - Fast, transparent, reproducible baseline.
   - Makes lexical dependence easy to test.
   - Model is not the contribution.
3. **Why high accuracy is not enough**
   - Unified accuracy: 97.7%; confirmed pilot: 97.0%.
   - Split may be easy, source-similar, or keyword-heavy.
   - No adversarial prompt rewrites in the original test.
4. **Research foundations**
   - TRAPD: AI vs human personalized SMS.
   - PhishFuzzer: seed-linked entity/length variants.
   - PromptBench: systematic prompt evaluation.
   - TextFooler/BAE/BERT-Attack/TextBugger: constrained text attacks.
   - SmishX: SMS context and explanation.
5. **Attack definition**
   - Safe transformation of wording/tone/format.
   - Same high-level intent and label.
   - Goal: test reliance on surface patterns.
6. **Prompt taxonomy**
   - P0 control; P1 SMS; P2 formal; P3 semantic; P4 lexical; P5 defanged; P6 public LLM; P7 seed-linked.
7. **Dataset package**
   - Source pool -> confirmed base -> variants -> results -> readable sample.
   - Provenance and license fields retained.
8. **Main experiment**
   - Select originally correct rows.
   - Freeze detector and threshold.
   - Compare before/after per sample and prompt.
9. **Metrics**
   - Recall, FNR, average probability, probability drop.
   - ASR = flips / originally detected phishing.
10. **Expected contribution**
   - Banking-focused, paired, prompt-ID benchmark.
   - Safety-aware and reproducible.
   - Mitigation results tied to observed failure modes.
11. **Next steps**
   - Import 91-row reviewed file.
   - Freeze 30-50 base rows.
   - Generate/collect approved variants.
   - Run detector and fill result table.

## 15. Overleaf Content

### Updated Research Question

This study asks: *How does prompt-based adversarial rewriting affect phishing-detector robustness on confirmed banking-related phishing messages?* We evaluate whether controlled changes to style, wording, length, and channel format reduce the performance of a frozen baseline detector while the high-level phishing intent and true label remain unchanged.

### Related Work: Prompt-Based Phishing and Adversarial Text Attacks

Prior research has compared human- and LLM-authored phishing, generated personalized smishing, assembled LLM phishing corpora, and developed explainable SMS-phishing detectors. PromptBench provides a framework for systematic prompt evaluation, while TextFooler, BAE, BERT-Attack, TextBugger, and DeepWordBug show that constrained semantic, contextual, and character perturbations can expose classifier weaknesses. PhishFuzzer further demonstrates seed-linked variants across controlled entity and length dimensions. These works motivate our protocol, but they do not jointly provide a confirmed-banking, paired prompt-rewrite benchmark for a frozen phishing detector.

### Dataset Construction

The project first standardized 11,186 SMS and email messages and identified 6,372 banking candidates through keyword filtering. Because keyword matches are not final topic labels, a priority sample was manually reviewed under stricter banking criteria. The prompt-attack base set will contain 30-50 confirmed banking phishing messages that the baseline originally classifies correctly. Provenance, channel, authorship, label, requested action, baseline probability, and selection rationale are retained. Sources with unclear redistribution rights are used only in local analysis.

### Prompt-Based Attack Methodology

We define a Prompt-Based Adversarial Rewriting Attack as a controlled transformation of wording, tone, format, or surface structure that preserves high-level phishing intent and the true label. Conditions P0-P7 cover an unchanged control, SMS style, formal notification style, semantic rewriting, lexical/character perturbation, defanging, approved public LLM-generated data, and licensed seed-linked variants. Generated examples use placeholders and omit operational details. Human review verifies intent preservation and safety before scoring.

### Evaluation Metrics

The frozen TF-IDF + Logistic Regression model is evaluated before and after transformation. We report recall, FNR, average phishing probability, probability drop, and ASR. ASR is the proportion of originally detected phishing inputs that become false negatives after transformation. Where appropriate, we report 95% confidence intervals and aggregate by prompt, channel, authorship, and source. Accuracy and precision are not interpreted as primary metrics on phishing-only subsets.

### Expected Contributions

The expected contributions are: (1) a confirmed banking-phishing base set; (2) a research-derived, safety-aware prompt taxonomy; (3) a paired detector-degradation benchmark; (4) prompt-level ASR and probability-shift results; (5) a provenance- and license-aware data package; and (6) mitigation experiments using augmentation, SMS-specific features, intent/action features, calibration, and tiered review.

### Limitations

The confirmed set is small and may contain few SMS examples. Human, LLM-generated, and SMS sources differ in channel and provenance, so unpaired authorship comparisons may be confounded. Intent preservation requires judgment, and automated similarity does not guarantee label preservation. TF-IDF results do not generalize automatically to transformer or deployed commercial detectors. Some useful public repositories lack explicit redistribution terms. Safe defanging may itself change detector signals, so it is analyzed as a distinct condition.

### Next Steps

Import the reviewed 91-row phishing-only file, verify its corrected labels and probabilities, freeze the 30-50-row base set, create approved P0-P7 variants, run the unchanged detector, compute ASR and confidence intervals, and then evaluate mitigations on the identical held-out variants.

## 16. Step-by-Step Action Plan

| Step | Use | Produce | Why | Supports |
|---:|---|---|---|---|
| 1 | Primary papers and repository links | `literature/literature_matrix.csv` | Establish verified methods and limits | Literature table |
| 2 | Literature matrix | `prompts/prompt_taxonomy.csv` | Fix prompt IDs, sources, safety, and metrics before generation | Prompt taxonomy |
| 3 | `confirmed_banking_phishing_only.csv` | `base_banking_phishing_set.csv` | Convert reviewed pilot into auditable attack inputs | Dataset construction |
| 4 | Base-set eligibility fields | 30-50 `selected_for_attack=yes` rows | ASR requires originally correct phishing | Base-set audit |
| 5 | Base set + taxonomy | `prompt_attack_variants.csv` | Preserve sample-prompt links | Variant inventory |
| 6 | Approved public variants or safe placeholder generation | Reviewed P0-P7 rows | Create harder, non-operational test conditions | Prompt comparison |
| 7 | Frozen model + variants | Predictions/probabilities | Isolate attack effect without retraining | Row-level evaluation |
| 8 | Predictions | `prompt_attack_evaluation_results.csv` | Store reproducible before/after results | Main results |
| 9 | Evaluation results | ASR/probability/FNR aggregates | Quantify degradation by prompt | Attack success table |
| 10 | All tables | Slides and Overleaf updates | Communicate method, evidence, limits, and contribution | Final presentation/paper |

## 17. Short Version to Tell Professor

I am keeping TF-IDF plus Logistic Regression as a transparent baseline, but the high accuracy is not my contribution and does not prove robustness. My new experiment selects 30-50 manually confirmed banking phishing messages that the baseline detects correctly, creates safe prompt-based variants under fixed categories P0-P7, and tests the same frozen detector again. I will report probability drop, false-negative rate, and Attack Success Rate for each prompt type. The new contribution is a banking-focused, paired, safety-aware prompt-attack benchmark, followed by mitigation tests. I will redistribute only data with clear permission and document analysis-only sources separately.
