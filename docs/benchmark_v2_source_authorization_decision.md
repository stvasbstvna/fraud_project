# Benchmark v2 source authorization decision package

No source below is automatically authorized for the final benchmark merely because it is present locally or public online.

| Source | Classification | Intended use | Evidence currently in repository | Construction | Public examples | Defanging |
|---|---|---|---|---|---|---|
| Benchmark v2 researcher-authored non-operational pilot | synthetic/constructed control; already authorized only for pilot calibration | schema, condition-logic, and review-workflow calibration | project-authored manifest; no third-party text or personal data; `final_benchmark_eligible=false` | pilot only; not final | no | placeholders remain defanged |
| SmishX | public research dataset with documented provenance; final use requires scope confirmation | possible source/reference for authorized real anchors | pinned repository commit and MIT repository license documented in `data/ATTRIBUTION.md`; source says rows were relabeled from public sources | requires confirmation that dataset content and transformations are covered | requires confirmation/attribution | yes |
| SmishTank | requires confirmation; should not be redistributed now | possible local research reference only | paper/project citation exists, but no explicit row-level redistribution license was found | local use only until permission is documented | no | yes |
| Existing Benchmark v1 banking test/rewrite data | should not be reused as Benchmark v2 confirmatory anchors without a separately approved contamination and provenance decision | historical v1 analysis | frozen v1 lineage; models may already be related to its source corpus | not approved for v2 final | no new public examples | yes |
| Uploaded GPT-4o CSV, bank-transaction workbook, PhishFuzzer, PhishOracle | should not be used | none in v2 | repository attribution explicitly says rows are not redistributed; authorization not established | no | no | yes if ever reviewed |
| New researcher-authored synthetic anchors | recommended candidate; requires researcher/faculty authorization record | final C0 anchors and controlled generation inputs | not yet constructed or signed off | only after manifest entry, privacy review, hash, and approval | only if sign-off explicitly permits | mandatory for every destination-like token |

For final authorization each manifest row must record source ID/reference, access date, SHA-256, license name and URL or signed internal usage basis, redistribution status, transformation permission, privacy-review result, attribution requirement, and permitted populations. The current free-text license column is evidence to review, not authority.
