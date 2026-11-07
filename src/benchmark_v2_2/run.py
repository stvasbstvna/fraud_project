"""Execute v2.2 source feasibility before any generation or detector scoring."""
import argparse
from collections import Counter
import json
import re
import pandas as pd
from .controls import defang, valid_institution
from .source_audit import ROOT, DATA, RESULTS, sha, save_json, save_csv, screen_families, capacity_bound
from .source_inputs import original_inputs
from src.benchmark_v2_1.pilot_sources import entity_hint
from src.benchmark_v2_1.pilot_templates import BRANDS

FINANCIAL = re.compile(r'\bbank(?:ing)?\b|\b(?:account|a/c|card|credit|debit|credited|debited|transfer|neft|upi|imps|rtgs|payment|transaction|balance|deposit|statement|refund|otp|zelle|paypal|chase|hdfc|icici|hsbc|santander|nationwide|barclays|natwest|lloyds|sbi|bofa|citibank|citi|unionbank|kotak|revolut|monzo)\b', re.I)
BRAND_SCREEN = re.compile('|'.join(r'\b'+re.escape(brand)+r'\b' for brand in BRANDS), re.I)


def financial_candidate(text):
    return bool(FINANCIAL.search(text) or BRAND_SCREEN.search(text) or re.search(r'\b\w+bank\b', text, re.I))


def references():
    result = []; ledger = []
    files = [('data/final/train_sms.csv', 'text', 'id', 'train_validation'),
             ('data/final/validation_sms.csv', 'text', 'id', 'train_validation'),
             ('data/rewrite_experiment/original_banking_test_frozen.csv', 'text', 'id', 'prior_benchmark'),
             ('data/benchmark_v2_1/source/frames.csv', 'defanged_text', 'frame_id', 'prior_benchmark'),
             ('data/benchmark_v2_1/source/pilot_48_candidates.csv', 'defanged_text', 'frame_id', 'prior_benchmark')]
    for name, text_col, id_col, kind in files:
        path = ROOT / name
        frame = pd.read_csv(path, keep_default_na=False, usecols=[text_col, id_col])
        ledger.append({'path': name, 'sha256': sha(path.read_bytes()), 'rows': len(frame), 'purpose': kind})
        result.extend({'text': defang(str(r[text_col]))[0], 'id': str(r[id_col]), 'kind': kind} for r in frame.to_dict('records'))
    # semantic_frames_pilot.jsonl contains abstract claims, not SMS bodies.
    # The materialized dry-run variants are the actual prior textual evidence.
    path = ROOT / 'data/benchmark_v2/pilot/variants_dry_run_pilot.jsonl'
    if path.exists():
        records = [json.loads(line) for line in path.read_text(encoding='utf-8-sig').splitlines() if line.strip()]
        for r in records:
            text = r.get('defanged_text') or r.get('original_text') or r.get('text')
            if not text: raise ValueError('Unrecognized prior v2 source schema')
            result.append({'text': defang(text)[0], 'id': r['variant_id'], 'kind': 'prior_benchmark'})
        ledger.append({'path': path.relative_to(ROOT).as_posix(), 'sha256': sha(path.read_bytes()), 'rows': len(records), 'purpose': 'prior_benchmark'})
    return result, ledger


def candidate_rows(records):
    from .source_audit import map_label
    rows = []
    for r in records:
        if not financial_candidate(r['text']): continue
        safe, spans = defang(r['text']); label = map_label(r['raw_label']); errors = []
        if r['channel'] != 'sms': errors.append('row_channel_unresolved')
        if r['license'] == 'MIT_upstream_pending': errors.append('upstream_rights_unresolved')
        if label == 'unknown': errors.append('spam_or_unknown_not_phishing')
        letters = [c for c in safe if c.isalpha()]
        if not letters or sum(c.isascii() for c in letters) / len(letters) < .95: errors.append('not_English_primary')
        if not 20 <= len(safe) <= 700: errors.append('not_SMS_like_length')
        if '\ufffd' in safe: errors.append('encoding_damage')
        institution = entity_hint(safe) or 'NONE'
        if not valid_institution(institution, safe): errors.append('invalid_institution_hint')
        # No banking-origin claim is inferred from ham; all remaining rows still
        # require fresh A/B review. This broad screen intentionally overestimates.
        rows.append({k: r[k] for k in ['source_id', 'source_row_id', 'raw_label', 'channel', 'real_vs_synthetic', 'license', 'source_url', 'source_sha256', 'version']} | {
            'frame_id': 'V22-' + sha((r['source_id']+'\n'+r['source_row_id']+'\n'+r['text']).encode())[:24],
            'original_text_sha256': sha(r['text'].encode()), 'safe_text': safe, 'candidate_label': label,
            'validated_label': '', 'banking_related': 'pending_semantic_review', 'institution_entity': institution,
            'product_or_service': '', 'requested_action': '', 'destination_type': '', 'destination_value_safe': '',
            'event_or_claim': '', 'amount': '', 'date_or_time': '', 'message_function': '',
            'typed_spans_json': json.dumps(spans, sort_keys=True), 'rule_errors': ';'.join(errors),
            'source_review_approved': False, 'review_mode': 'automated_not_run'})
    return rows


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--offline', action='store_true')
    args = parser.parse_args()
    records, sources = original_inputs(args.offline)
    rows = candidate_rows(records)
    uci_hashes = {r['original_text_sha256'] for r in rows if r['source_id'] == 'UCI-SMS'}
    for r in rows:
        duplicate_origin = r['source_id'] == 'MENDELEY-SMISH' and r['original_text_sha256'] in uci_hashes
        r['source_group'] = 'UCI-LINEAGE' if r['source_id'] == 'UCI-SMS' or duplicate_origin else r['source_id']
        r['source_lineage_basis'] = 'exact_original_text_sha256_match_to_UCI' if duplicate_origin else 'source_identity_pending_upstream_review'
    ref, ledger = references()
    print(f'Source audit: {len(records)} original/local rows, {len(rows)} broad financial candidates; screening against {len(ref)} references', flush=True)
    # A control-only capacity preflight is deliberately optimistic: omitted
    # positive-candidate bridges could only merge/quarantine more controls.
    # There is no reason to spend hours clustering 20k phishing candidates when
    # even all available control families cannot meet the source minimum.
    controls = [r for r in rows if r['candidate_label'] == 'legitimate']
    screen_families(controls, ref)
    for r in rows:
        r.setdefault('template_family_id', '')
        r.setdefault('overlap_kind', '')
        r.setdefault('overlap_reference', '')
        r['family_screen_status'] = 'screened_control_preflight' if r['candidate_label'] == 'legitimate' else 'not_run_positive_family_preflight'
    for r in rows:
        if r['overlap_kind']:
            r['rule_errors'] = ';'.join(filter(None, [r['rule_errors'], r['overlap_kind'] + '_family_overlap']))
    bound = capacity_bound(rows)
    if bound['maximum_legitimate_before_semantic_review'] >= 16:
        # A passing preliminary bound is insufficient: run the full screen.
        rows = screen_families(rows, ref)
        for r in rows:
            r['family_screen_status'] = 'screened_full_pool'
            if r['overlap_kind'] and r['overlap_kind'] + '_family_overlap' not in r['rule_errors']:
                r['rule_errors'] = ';'.join(filter(None, [r['rule_errors'], r['overlap_kind'] + '_family_overlap']))
        bound = capacity_bound(rows)
    save_csv(DATA / 'source/candidate_audit.csv', rows)
    save_json(DATA / 'source/source_registry.json', sources)
    save_json(DATA / 'source/reference_manifest.json', ledger)
    counts = []
    for sid in sorted({r['source_id'] for r in rows}):
        for label in sorted({r['candidate_label'] for r in rows if r['source_id'] == sid}):
            selected = [r for r in rows if r['source_id'] == sid and r['candidate_label'] == label]
            usable = [r for r in selected if not r['rule_errors']]
            counts.append({'source': sid, 'candidate_label': label, 'broad_candidates': len(selected),
                           'rule_clear_rows': len(usable), 'rule_clear_families': len({r['template_family_id'] for r in usable if r['template_family_id']}),
                           'family_screen_status': selected[0]['family_screen_status'],
                           'automatically_semantically_approved': 0, 'final_frozen_sources': 0})
    save_csv(RESULTS / 'source_audit_counts.csv', counts)
    rejected = Counter(e for r in rows for e in r['rule_errors'].split(';') if e)
    summary = {'status': 'V2.2 SOURCE COHORT INSUFFICIENT' if not bound['source_capacity_sufficient'] else 'SOURCE_CAPACITY_PASSES_REQUIRES_FRESH_SEMANTIC_REVIEW',
               'input_rows_inspected': len(records), 'broad_financial_candidates': len(rows),
               'rule_clear_candidates': sum(not r['rule_errors'] for r in rows),
               'rule_rejection_reasons_nonexclusive': dict(sorted(rejected.items())), 'capacity_bound': bound,
               'source_cohort_frames': 0, 'source_cohort_frozen': False, 'source_semantic_review_calls': 0,
               'generation_calls': 0, 'detector_predictions': 0,
               'source_candidate_audit_sha256': sha((DATA / 'source/candidate_audit.csv').read_bytes()),
               'capacity_scope': 'financial-keyword and known-institution candidate pool only; not proof that no further banking sources exist',
               'validation_type': 'deterministic_source_feasibility_only_not_semantic_approval',
               'independent_human_annotation': False}
    save_json(RESULTS / 'source_summary.json', summary)
    if not bound['source_capacity_sufficient']:
        save_csv(DATA / 'frozen/source_cohort.csv', [], ['frame_id', 'validated_label', 'safe_text', 'source_id', 'template_family_id'])
        save_json(DATA / 'frozen/source_cohort_manifest.json', {'status': 'NOT_FROZEN_SOURCE_COHORT_INSUFFICIENT',
                  'rows': 0, 'source_audit_sha256': summary['source_candidate_audit_sha256'],
                  'reason': 'Optimistic control capacity is below 16 under <=25% synthetic controls and <=50% per source lineage within class.',
                  'source_cohort_sha256': sha((DATA / 'frozen/source_cohort.csv').read_bytes())})
        stages = [{'stage': stage, 'status': 'NOT RUN', 'reason': 'Source minimum gate failed before generation'} for stage in
                  ['fresh_machine_source_review', 'accepted_source_freeze', 'condition_eligibility', 'prompt_prevalidation', 'generation', 'rewrite_review', 'manipulation_validation', 'benchmark_freeze', 'detector_scoring', 'paired_statistics', 'scientific_figures']]
        save_csv(RESULTS / 'stage_status.csv', stages)
        print(json.dumps(summary, indent=2))
        return 2
    # This source audit does not pretend to implement a successful experiment.
    # Reaching this branch requires the next reviewed implementation, not scoring.
    print(json.dumps(summary, indent=2))
    return 3


if __name__ == '__main__':
    raise SystemExit(main())
