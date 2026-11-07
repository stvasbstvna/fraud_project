# Benchmark v2 preregistration protocol

## Status and scope

Benchmark v2 is a protocol-design artifact. No v2 messages have been generated and no frozen detector has been run on v2. Benchmark v1 remains a separate, unchanged paired neutral-rewrite pilot (156 originals, 153 completed rewrites, three safety-check rejections, human review in progress). A robustness gap may or may not be found; conclusions must follow measured evidence.

**Primary research question:** How do controlled changes in fluency, lexical form, conversational naturalness, and action explicitness affect the predictions and confidence of frozen banking-smishing detectors while semantic intent and requested action remain constant?

**Provisional contribution:** This study introduces a controlled, leakage-resistant paired benchmark for identifying which linguistic transformations cause banking-smishing detectors to change confidence or cross decision boundaries.

## Leakage firewall and analysis freeze

Before generation, prompts, schemas, exclusions, validation thresholds, population assignments, and analysis code versions will be frozen and hashed. The generator and any semantic auditor must never receive detector predictions, probabilities, vocabulary, coefficients, feature importances, thresholds, errors, or false-negative examples chosen because they fooled a detector. Prompts will not be revised after detector performance is observed. Variants will not be generated, retained, regenerated, excluded, or selected based on detector outcomes. Detector evaluation begins only after non-detector quality exclusions and human-review decisions are frozen. Any later exploratory work must be labeled and kept out of confirmatory results.

## Populations, accounting, and unit of independence

Counts are not frozen. Three populations are accounted separately: (1) the completed 48-scenario prompt-development pilot, stored outside Benchmark v2 and never analyzed; (2) quality-validation scenarios used to freeze prompts, thresholds, and review operations but excluded from confirmatory inference; and (3) untouched confirmatory final-test scenarios. Power is based only on unique final-test phishing and legitimate `scenario_id` values—not a total before a 60/20/20 split. Quality and confirmatory counts remain explicit human decisions until power, exclusion, and review assumptions are justified. Conditions, replicates, quality scenarios, pilot scenarios, and fully crossed generator variants do not add independent confirmatory units.

`scenario_id` is the unit of independence. `scenario_family_id` links matched phishing and legitimate scenarios and must stay within one population. All variants of a scenario remain grouped during review, bootstrapping, intervals, and models.

## Controlled conditions

- `C0_template`: short, recognizably template-like banking SMS realization.
- `C1_fluent`: grammar, spelling, punctuation, and basic coherence corrected with minimal lexical or structural change.
- `C2_natural`: plausible contemporary SMS with meaningful lexical and syntactic variation while the frame is fixed.
- `C3_natural_softened`: natural realization whose action wording is less abrupt or formulaic, while action, channel, intent, label, entities, and scenario remain fixed.

`C3` changes action explicitness as well as naturalness; it must not be merged with `C2` for causal interpretation. Every variant records fluency, lexical variation, syntactic variation, conversational naturalness, action explicitness, urgency, personalization, length, URL presence, tactic, and requested-action type. Simultaneous changes are permitted only when specified by the condition and recorded.

### Generation lineage and generator assignment

`C0` is the anchor. Its `creation_method` states whether it is public-source, transformed-real, human-authored, deterministic-template, or LLM-generated. Non-LLM anchors use JSON `null` for provider/model/version/temperature/response ID—never invented `not_applicable` metadata. `C1` and `C2` derive independently from C0; C3 derives from C2.

The versioned `generator_pool` freezes block ID, provider, model, exact version, access method, seed behavior, temperature, structured-output support, assignment weight, and active status. Seeded stratified scenario-level assignment selects one active block to produce C1/C2/C3, balanced across label, event, action, source type, and population. Generator cannot be confounded with condition. An optional fully crossed subset adds no independent-scenario credit.

## Confirmatory outcome and family

The confirmatory primary outcome is **binary phishing prediction at the detector's frozen threshold**. H1 estimates paired recall difference C2 minus C0; H3 estimates paired recall difference C3 minus C2. Transition tables describe discordant observations underlying these effects. H2 compares `I(prediction_C0 != prediction_C2) - I(prediction_C0 != prediction_C1)` per scenario; standardized within-model score change is secondary.

H1, H2, and H3 are tested independently for both frozen detectors, and H4 is one detector-interaction test: seven primary tests. Holm correction controls familywise α=0.05 across all seven. This family is frozen without reference to v2 performance.

## Semantic scenario construction

Frames specify canonical intent, communicative goal, structured facts, critical invariants, transaction type/status, account/card context, requested-information type, and non-operational placeholders: `[BANK]`, `[MERCHANT]`, `[AMOUNT]`, `[CURRENCY]`, `[DATE]`, `[REFERENCE_ID]`, `[DEFANGED_URL]`, and `[PHONE_PLACEHOLDER]`. Placeholder presence is symmetric across frame invariants and text. No live/www/non-defanged domain, email, real phone, credential, account number, payment destination, or personal information is allowed.

Every frame references a source-manifest entry with source URL/reference, access date, hash, license evidence, redistribution status, transformation permission, privacy review, and attribution requirement. Free-text license notes alone never authorize inclusion.

### Banking-event taxonomy

The extendable core is unusual transaction; card lock/restriction; card delivery; payment confirmation; transfer confirmation; refund; account-profile update; fraud review; one-time security code; branch/appointment notice; statement availability; replacement card; direct-deposit notice; subscription/recurring-payment alert; and documented `other`. Events may have phishing and legitimate counterparts. Bank-themed content is not automatically phishing.

### Requested action and channel

Actions are: no action, review information, confirm/deny transaction, sign in, follow link, call number, reply by SMS, visit branch, wait for further communication, and provide information. Action is distinct from channel (`none`, message, web, phone, SMS reply, in person, banking app, unspecified).

### Tactics

Authority, urgency, fear/loss avoidance, scarcity, reward, helpfulness, routine notification, reassurance, social proof, and no persuasion tactic. Strong urgency is not required for phishing.

## Legitimate controls and matching

Legitimate messages are necessary to measure specificity, false-positive rate, balanced accuracy, MCC, and calibration; high phishing recall can coexist with unusably weak specificity. Phishing and legitimate frames will be matched or stratified where possible on banking event, bank entities, length, URL and amount presence, security vocabulary, urgency, and requested action. Residual imbalance will be reported rather than concealed.

## Population assignment

Prompt-development pilots are outside Benchmark v2. Included scenario families are assigned either to quality validation or untouched confirmatory final test; no random 60/20/20 accounting is used. All conditions/replicates for a scenario and all matched scenarios in a family share a population. Exact and near-duplicate families cannot cross populations. Frozen detectors are evaluated only after protocol/quality freeze and only on confirmatory final test for confirmatory claims.

## Quality validation

1. **Deterministic:** schemas, unique IDs, lineage, generator blocks, conditions, symmetric placeholders, active/www/non-defanged domains, emails, phones, amounts, entities, valid length ranges, duplicates, and scenario/family population leakage.
2. **Independent automated/LLM-assisted semantic audit (optional):** intent, action, label, entities, operational safety, condition difference/fit, and naturalness. This is never called human review and receives no detector output.
3. **Blinded human review:** hide condition where practical and always hide detector results; approve/reject/uncertain with reasons. A stratified 10–20% receives a second independent review. Report raw agreement and Cohen's kappa where applicable; disagreements are adjudicated by a reviewer who sees both rationales but no detector results.

Exclusions use the preregistered list in the review rubric and occur before detector evaluation whenever possible. Correct or incorrect detector classification is never an exclusion reason.

Validation is condition-specific: C0 requires template fidelity; C1 correction fidelity; C2 naturalness plus preservation; and C3 naturalness, preservation, and a verified reduction on the blinded 1–5 action-explicitness scale relative to paired C2. There is no global naturalness exclusion threshold.

## Reproducibility and freeze record

Configuration, schemas, prompt IDs/versions, source manifests, population manifest, deterministic validation report, human-review audit, exclusion log, package lock, and file hashes will be archived. Random operations use the configured seed. The inactive OpenAI model snapshot in the generator decision package is a reproducibility-based recommendation and requires explicit pre-generation approval; provider selection is not required by either data schema.

Related documents: [hypotheses](benchmark_v2_hypotheses.md), [power analysis](benchmark_v2_power_analysis.md), [analysis plan](benchmark_v2_analysis_plan.md), [review rubric](benchmark_v2_review_rubric.md), and [provenance/ethics](benchmark_v2_provenance_and_ethics.md).
