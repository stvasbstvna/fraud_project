# Pilot source selection — prospective rules and decisions

This is an additive selection/review extension to the existing pipeline. No original prompt, generator configuration, frozen detector, master candidate file or earlier benchmark result is modified. No detector score is read for selection. Current candidate files are **not ground truth**.

## Original-source retrieval

`python -m src.benchmark_v2_1.pilot_sources` retrieves originals, not aggregate SMISH_DT message copies:

- Mendeley v1 `Dataset_5971.zip`: publisher SHA-256 `9bbf3188fdad81495d8e82825648b9b63b53fc86841a3d26c02629990b233cc3`, CSV member SHA-256 `649844f1c62a6b27e145eaf17a65f7010c56c390e11a794ea8329993a05ba71e`. 5,971 rows; case-normalized labels: ham 4,844, smishing 638, spam 489. Original [record/license](https://data.mendeley.com/datasets/f45bkkt8pr/1) is CC BY 4.0. Attribute Mishra and Soni (2022), DOI 10.17632/f45bkkt8pr.1; safe redaction/filtering are project modifications.
- Gateway commit `a4f18cedc9909cbf8234eea3c2028080a1e95cd4`, original CSV SHA-256 `d125c394af792faeb2b71b3f7100cad3b4cece02aff78cb4ec1fb9e7db90f230`: 68,029 rows. [Original repository](https://github.com/wspr-ncsu/sms-phishing) has MIT licensing and explicitly describes research reuse of code/data. Full MIT notice is retained in `source/pilot_gateway_LICENSE.txt`, original README in `pilot_gateway_README.txt`. Repository license is not proof of message label validity: VirusTotal/APWG evidence still requires message-level review. Attribute Nahapetyan et al., IEEE S&P 2024, and wspr-ncsu copyright.
- [UCI original archive](https://archive.ics.uci.edu/dataset/228/sms+spam+collection): SHA-256 `1587ea43e58e82b14ff1f5425c88e17f8496bfcdb67a583dbff9eefaf9963ce3`, 5,574 parsed lines, ham 4,827/spam 747. CC BY 4.0; attribute Almeida/Hidalgo (2011), DOI 10.24432/C5CC84. Only potential legitimate bank-notification controls are considered; UCI spam never maps to phishing.

Source archive bytes are examined in memory. Persisted message bodies are defanged; raw message SHA-256 and original row IDs support traceability. Account/reference-like long numbers and dataset masks remain placeholders. No source links or telephone destinations are activated. Publisher/source provenance URLs are metadata, not message destinations.

SmishTank, SmishX, SpamHunter and Super remain HOLD under the existing registry: unclear row-level license scope/labels and/or frozen training overlap are not solved by public visibility. None enters this selected cohort. Earlier source audit documentation is preserved as a dated record, not silently updated to claim these new downloads happened earlier.

## Source schema trap and archived attempts

Gateway's header names six fields while all 68,029 data rows contain seven. pandas' default parser silently infers the first field as index, shifting `messageID` and `message`. An initial current-run audit made that error. Regression-tested `parse_gateway` now requires the exact audited header/row widths, verifies unique message IDs, and reads the first four verified ordinal fields. The extra trailing metadata is not assigned an invented meaning. Superseded current-run audit/selection outputs are retained under `diagnostics/pilot_attempt1_superseded/` and `pilot_attempt2_superseded/`; use only the final top-level pilot diagnostics for current counts. No historical benchmark output was overwritten to correct this.

## Candidate triage

Financial/bank keyword and institution screening is **candidate retrieval**, not label evidence. English screening requires at least 95% ASCII among letters and two common English tokens; it is a conservative heuristic, not verified language identification. SMS-like length is 20–700 characters. Damaged encoding, unknown/spam labels, unresolved endpoints and failed screens are held with recorded reasons. Ham requires an explicit bank-origin notification/security-reminder/transaction-confirmation pattern, so personal banking chat or telecom top-ups do not fill the control quota. False negatives of this screening remain possible.

Phishing source labels are recorded as `candidate_label`; `true_label`, `intent`, `requested_action` and `destination` remain blank pending review. Source-level smishing flags can be wrong: a payment notice that appears legitimate must be adjudicated, not accepted from its CSV label. Do not infer legitimacy from detector output. Entity/category values are provisional string matches; examples such as “Dear Sir Your Bank” require correction/rejection during Stage A.

Legacy synthetic negatives remain unapproved review candidates. Legacy synthetic positives are not reused to fill the pilot because their malicious intent was not established. No new source messages are authored in this run.

## Template control: pilot-template-v2

Normalize HTML masks, bracketed placeholders, numeric amounts/dates/references, literal/provisionally recognized bank names, whitespace and punctuation. Known notification event phrases in the legacy authoring script are treated as explicit template slots; changing deposit/card/statement/security event text alone does not create an independent template. This normalization changes only diagnostic representations, never C0 source text.

For normalized token sets compute Jaccard `J`; for normalized strings compute SequenceMatcher structural similarity `S` (autojunk=False). Join an undirected edge if `(J ≥ .80 and S ≥ .80) or (J ≥ .45 and S ≥ .92)`, including exact normalized equality. Connected components define families, including conservative transitive merges. Hash the version and sorted unique normalized component members to get reproducible family IDs independent of row order. IDs are tied to the audited pool/version; adding data can merge components.

Before selection, compare candidates against train and validation text using the same normalization/rules and exclude any matching training family witness. Scores/predictions/features never enter this screen. Diagnostics record the highest-similarity compatible witness (stable-ID tie break); if no compatible match exists, they record the nearest screened reference. Family detection is heuristic: undetected paraphrases and overly broad transitive components remain possible. Stage A explicitly reviews family independence.

## Selection policy and limitations

From selectable candidates, alternate proposed labels toward 24 each. Pick underrepresented category/source/entity first with deterministic frame-ID tie breaking. One frame per template family; at most four per case-folded entity or label/category, at most 24 per source (the full 48 target implies no majority source). Do not fill a deficit with HOLD rows, repeated templates or personal chat. Unknown entity hints are grouped conservatively rather than counted as different banks.

The **reduced candidate queue does not satisfy the 48-frame pilot specification**. Its source share may exceed 50% and synthetic controls may remain confounded with label; those are explicit blockers, not waived requirements. Add appropriate licensed independent control frames, or obtain a prospective reduced-cohort protocol amendment before interpretation. Stage A approval alone cannot authorize generation of an incomplete/imbalanced cohort. Current readiness gate requires 48 reviewed frames, agreed 24/24 labels, unique validated families, source diversity and reviewed entity balance; no retrospective design change based on scores.

## Review boundary and commands

`pilot_review` creates two Stage A assignments per selected source, with source evidence digest, blank semantic annotations and explicit pending decisions. It separately creates an empty Stage B rewrite-review schema; it never fabricates missing rewrite texts or review outcomes. Source and rewrite review fields are distinct tasks.

```powershell
.\.venv\Scripts\python.exe -m src.benchmark_v2_1.pilot_sources
.\.venv\Scripts\python.exe -m src.benchmark_v2_1.pilot_selection
.\.venv\Scripts\python.exe -m src.benchmark_v2_1.pilot_review
.\.venv\Scripts\python.exe -m src.benchmark_v2_1.pilot_review --reviews data/benchmark_v2_1/review/pilot_source_review.csv
```

First three commands create exclusive outputs; reproduce them in a clean run/copy rather than overwriting existing evidence. The fourth is read-only and can be rerun on genuine completed decisions. Do not replace a `pending` value with invented approval. Formal source import into the existing canonical generation schema remains downstream work after actual human approvals and final cohort design; the new Stage A checker does not silently manufacture old semantic-preservation checkboxes to bypass that boundary.
