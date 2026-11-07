# Benchmark v2 provenance, licensing, and ethics policy

## Source classes

- **Real public data:** catalog metadata first; ingest only after documented license, redistribution terms, intended use, and attribution requirements are verified.
- **Transformed real examples:** retain source reference, transformation lineage, license compatibility, and duplicate group. Transformation does not erase original rights or privacy obligations.
- **Fully synthetic frames:** label as synthetic and document authoring/generation method; synthetic status does not guarantee safety or freedom from memorized content.

Downloadability is not permission to reuse or redistribute. Unverified third-party data stays outside Git. Every included frame records source type, reference, provenance, license, and timestamp; attribution lives with the release manifest.

Every frame must reference a validated source-manifest entry containing source ID, URL/reference, access date, SHA-256, license name and URL, redistribution status, transformation permission, privacy-review status, and attribution requirement. Inclusion requires `redistribution_status=permitted` and `privacy_review_status=passed`; transformed-real frames additionally require `transformation_permission=permitted`. An arbitrary free-text `license` value in a semantic frame is descriptive only and never authorizes inclusion or redistribution.

## Privacy and operational safety

Remove personal information and credentials. Replace entities/destinations with the approved bracketed placeholders. Reject active URLs, real phone numbers, account identifiers, payment destinations, and newly introduced amounts/facts. Do not send messages or interact with real people/services. Repository examples remain defanged and research-only.

## Duplicates and contamination

Hash exact/canonical text and cluster near-duplicate scenarios before splitting. Search train/reference corpora for contamination where licensing permits, document methods and uncertainty, and prevent duplicate clusters crossing splits. Benchmark v2 final test cannot overlap detector training data. Scenario lineage prevents multiple transformations being counted as independent sources.

## Leakage and independence

Generator/auditor inputs exclude all detector predictions, probabilities, features, weights, importance scores, thresholds, errors, and detector-selected failures. Prompts/exclusion rules freeze before detector evaluation. No performance-conditioned generation, selection, regeneration, or exclusion is permitted. Human reviewers are blinded to detector results.

Prompt-development pilots are stored outside Benchmark v2. Quality-validation and confirmatory-final-test scenario families cannot overlap. `scenario_family_id` keeps matched phishing/legitimate counterparts together. Generator assignment occurs at scenario level: the same declared generator block produces C1, C2, and C3, balanced across design factors. Optional crossed-generator variants retain their original scenario cluster and add no independent sample credit.

## Release and governance

Release only records with verified redistribution authority, completed safety checks, and appropriate attribution. Maintain an exclusion/audit log without sensitive raw content. Record changes as new dataset versions; never silently replace frozen test content. Benchmark v1, existing splits, and model artifacts remain separate and unchanged.
