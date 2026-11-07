# Benchmark v2 draft-to-final transition gates

## Prompt package

`PROMPT_FINALIZABLE = false` while any of the following is incomplete:

- generator provider/model/exact version and decoding package approved;
- final source classes and condition vocabularies approved;
- C1 closed list reflected consistently in prompt, protocol, schema, and validator;
- C3 aggregate manipulation threshold and agreement statistic approved;
- pilot review and required adjudication completed successfully;
- prompt IDs/version selected and immutable text SHA-256 recorded;
- researcher and faculty-mentor sign-off recorded.

When every item is satisfied, preserve the draft, create `docs/benchmark_v2_prompt_package_FINAL.md`, update references atomically, assign a non-draft version, run tests/readiness, and record hashes. Do not silently rename the draft in place.

## Generation lock

`GENERATION_UNLOCKABLE = false` while any of the following is incomplete:

- `PROMPT_FINALIZABLE` is false;
- no active positive-weight generator block;
- final source manifest lacks authorization evidence or verified hashes;
- final scenario counts/distributions and generator assignment manifest are not frozen;
- confirmatory power assumptions and N are not approved;
- technical and full readiness are not both true;
- sign-off form does not expressly authorize detector-blinded generation.

Only after all gates pass may `DRAFT_DO_NOT_GENERATE` be replaced with a versioned frozen state. Removing the flag does not authorize detector evaluation; that requires a separately frozen, reviewed final dataset.
