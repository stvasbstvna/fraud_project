# Sting9 access and license audit

Status: **BLOCKED**. License: **CONFLICTING**. No Sting9 records were downloaded or included in modeling. No raw redistribution is permitted by this benchmark pending resolution.

Audited by read-only HTTPS GET on 2026-11-07T03:24:42.042534+00:00. Exact response times, URLs, HTTP codes, byte counts and SHA-256 values are in `data/benchmark_v3/provenance/sting9/http_manifest.json`; local artifact hashes are in `snapshot_hashes.json`. These are actual retrievals, not inferred availability. Cached snapshots and script-free extracted text are retained for private research audit; website snapshots should not be redistributed as dataset assets.

## License evidence

| Current page | Observed statement |
|---|---|
| https://sting9.org/dataset | ?Creative Commons CC0 (Public Domain)?; body permits commercial use and says no attribution required. Its own footer instead says ODC-BY-NC. |
| https://sting9.org/ | Body calls it a CC0 public dataset; separate license section and footer say ODC-BY-NC, described as attribution/noncommercial research access. |
| https://sting9.org/research/api-docs | Swagger container with footer ODC-BY-NC; its current route JavaScript references `/api-docs.json`. |
| https://sting9.org/api-docs.json | API v1.0 metadata names ?Creative Commons CC0? and separately links the site's terms of service. |
| https://sting9.org/terms | Effective date November 12, 2025. Section 4.1 names ODC-BY-NC with clarifications. |
| https://sting9.org/license | ?Based on Open Data Commons Attribution-NonCommercial (ODC-BY-NC) with Clarifications?. |

The retrieved license permits noncommercial academic benchmarks with freely published results, requires attribution, a license link and disclosure of changes, and requires open results under compatible licenses. It restricts commercial model training, proprietary deployment, paywalled results and certain industry-sponsored uses. This is a description of the retrieved custom terms, not an assumption that a standard license identifier resolves them. The project's eligibility for all conditions was not established; metadata-only auditing proceeds, with no dataset analysis. Terms and license wording take precedence for conservative exclusion until the provider resolves the conflicting CC0 claims.

## Access attempts in required order

1. `GET https://api.sting9.org/api/v1/export` returned HTTP **401**, exact body `{"error":"Unauthorized","message":"Missing authorization header"}`. No matching STING9 keys existed in process environment or repository root `.env`; no credentials were printed, created or invented. Swagger requires Bearer authentication and researcher/partner role for export.
2. The exact dataset-page download anchor is `https://github.com/sting9/dataset`. GET returned HTTP **404**. The unrelated footer organization link was not substituted. There is no valid dump to pin: repository commit, dump timestamp and dump hash are unavailable, rather than fabricated. The 404 page itself is hashed as evidence.
3. Swagger documents `GET /submissions` with only `page` and `page_size`; authentication is required. A single minimal `GET .../submissions?page=1&page_size=1` returned HTTP **401**, with the same exact error body. No pagination continued. `message_type=sms` and `detected_language=en` are **not documented query filters in the current specification**, so they were not invented or sent. If future authorized access exists, filter actual `type=sms` and `language=en` locally, retaining original fields.

No registration, login, submission, bulk submission, refresh POST or other state-changing endpoint was called. Zero records means no observed channel distribution; it does not mean the upstream dataset is empty.

## Current documented API and schema

Swagger 2.0 host `api.sting9.org`, base path `/api/v1` confirms the current API base. The dataset examples separately use `/v1/submissions`, an inconsistency; access probes used the actual Swagger base.

- GET `/export`: format json/csv/jsonl, default json; page default 1; page_size default 100, maximum 1000; start_date/end_date RFC3339; type/category filters. Authenticated researcher/partner access.
- GET `/submissions`: page default 1, page_size default 20; Bearer authentication. List response fields page, page_size, submissions, total, total_pages.
- GET `/stats`: aggregate statistics, no security requirement declared. Not needed for record acquisition and not probed.
- Authentication endpoints are POST `/auth/login` and POST `/auth/register`; inspected as documentation only.
- Dataset page advertises **1000 requests/hour**. Swagger does not state a separate rate limit. This audit made only one export and one submissions request, and caches responses to avoid redownloads.

Current `SubmissionResponse` schema: `id`, `type`, `category`, `content`, `anonymized_content`, `created_at`, `processed_at`, `language`, `status`, `metadata`. Metadata schema: `attachments`, `date`, `from`, `headers`, `phone_number`, `subject`, `to`, `urls`. Status enum: pending, processing, processed, flagged, approved, rejected. Supported channels include email, sms, whatsapp, telegram, signal, social_media, other.

The requested research field names are not promised by this schema. Future ingestion may preserve `id` as submission_id, `type` as message_type, `language` as detected_language, original content fields, and created_at separately as submission timestamp. `metadata.date` must be quality-audited before treating it as message time. Category/status are retained raw; neither automated category nor processing status establishes an independently verified label. Threat level, confidence score, claimed sender, detected country, verified flag and SMS urgency are not guaranteed here. Missing values must remain missing; confidence never becomes ground truth.

## Disposition and next action

Sting9 contributes **0 records**, **0 English SMS**, and **0 training/test rows**. Continue the other sources. Provider-side remediation is an available official dump or authorized existing researcher/partner access, plus explicit reconciliation of license terms and project eligibility. Do not request new credentials or register automatically. Re-audit access and permissions before future data ingestion; preserve raw provenance locally and keep redistribution disabled while the conflict remains.
