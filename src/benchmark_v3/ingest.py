"""Pinned per-source ingestion, rights-gated candidate exports and exact origins."""
from datetime import datetime, timezone
import importlib
import json
import subprocess
from collections import Counter
from .core import ROOT, DATA, RESULTS, digest, safe_text, label_candidate, financial_candidate, exact_dedup, save_csv, save_json

REPO = ROOT/'external/SMISH_DT'
SOURCES = [
    ('mendeley', 'Mendeley_Dataset_5971.csv', 'sms', 'en_screen_required'),
    ('uci', 'UCI_SMSSpamCollection', 'sms', 'en_screen_required'),
    ('gateway', 'sp24-smishing/phishing_messages.csv', 'sms', 'en_screen_required'),
    ('nus', 'Singapore_smsCorpus_en_2015.03.09_all.json', 'sms', 'en_collection'),
    ('smishtank', 'smishtank.csv', 'sms', 'en_screen_required'),
    ('spam_hunter', 'SPAM-Hunter_full_dataset_messages.csv', 'sms', 'en_screen_required'),
    ('super_sms', 'super_sms_dataset.csv', 'sms', 'en_screen_required'),
    ('exais', 'ExAIS_SMS Spam Dataset/all_ExAIS_SPAM_Dataset.csv', 'sms', 'mixed')]


def verify_git_blob(raw, expected):
    import hashlib
    for value, method in [(raw, 'exact_git_blob'), (raw.replace(b'\r\n', b'\n'), 'git_checkout_CRLF_only')]:
        if hashlib.sha1(f'blob {len(value)}\0'.encode()+value).hexdigest() == expected:
            return method
    raise ValueError('Worktree source differs from pinned Git object beyond checkout line endings')


def english(text):
    letters = [c for c in text if c.isalpha()]
    return bool(letters) and sum(c.isascii() for c in letters)/len(letters) >= .95


def main():
    revision = subprocess.check_output(['git', '-C', str(REPO), 'rev-parse', 'HEAD'], text=True).strip()
    rights_list = json.loads((DATA/'provenance/upstream_rights_evidence.json').read_text(encoding='utf-8-sig'))['sources']
    rights = {r['source_id'].replace('spamhunter', 'spam_hunter'): r for r in rights_list}
    stamp_path = DATA/'provenance/smish_dt_manifest.json'
    when = json.loads(stamp_path.read_text())['retrieval_timestamp_utc'] if stamp_path.exists() else datetime.now(timezone.utc).isoformat()
    registry = []; file_ledger = []; audit = []; financial = []
    for sid, name, channel, language in SOURCES:
        path = REPO/'Dataset'/name
        raw = path.read_bytes()
        source_sha = digest(raw)
        if raw.startswith(b'version https://git-lfs.github.com/spec/v1'):
            raise ValueError(f'Required source remains an LFS pointer: {name}')
        # Verify exact file bytes against the pinned git object, not merely a
        # hash of an unaudited worktree copy. No source files are rewritten.
        expected = subprocess.check_output(['git', '-C', str(REPO), 'rev-parse', f'{revision}:Dataset/{name}'], text=True).strip()
        identity_method = verify_git_blob(raw, expected)
        rows = importlib.import_module('.sources.'+sid, __package__).read(path)
        r = rights[sid]; allowed = r['modeling_allowed'] is True
        text_license = r.get('license', '')
        registry.append({'source_id':sid, 'aggregator':'SMISH_DT_discovery_and_pinned_copy', 'original_dataset':sid,
             'original_url':r['original_url'], 'retrieved_from':f'https://github.com/MarazMia/SMISH_DT/blob/{revision}/Dataset/{name}',
             'retrieval_date':when, 'source_version':revision, 'commit_sha':revision, 'file_sha256':source_sha,
             'channel':channel, 'language':language, 'original_label_schema':json.dumps(dict(Counter(x['raw_label'] for x in rows)), sort_keys=True),
             'candidate_label_mapping':'Explicit smishing/phishing -> phishing candidate; all other labels uncertain until semantic review',
             'license_text':text_license, 'license_status':r['license_status'], 'redistribution_allowed':r['redistribution_allowed'],
             'notes':r.get('label_policy','')+'; '+r.get('conditions','')})
        file_ledger.append({'path':'Dataset/'+name, 'sha256':source_sha, 'git_blob':expected, 'git_identity_method':identity_method, 'bytes':len(raw), 'rows':len(rows)})
        count_en = 0; count_financial = 0
        for row in rows:
            is_en = english(row['text']); count_en += int(is_en)
            if not is_en or not financial_candidate(row['text']): continue
            count_financial += 1
            financial.append(row | {'id':sid+'-'+row['source_row_id'], 'source_id':sid, 'channel':'sms', 'language':'en_screened',
                'origin_type':'uncertain' if sid=='gateway' else 'real_source_candidate', 'candidate_label':label_candidate(row['raw_label']),
                'modeling_allowed':allowed, 'original_text_sha256':digest(row['text']), 'safe_text':safe_text(row['text']),
                'source_file_sha256':source_sha, 'source_url':r['original_url']})
        audit.append({'source_id':sid, 'raw_rows':len(rows), 'english_SMS_candidates':count_en,
                      'financial_candidates':count_financial, 'modeling_allowed':allowed,
                      'raw_labels_json':json.dumps(dict(Counter(x['raw_label'] for x in rows)),sort_keys=True)})
        print(f'{sid}: {len(rows)} raw, {count_en} English-screened, {count_financial} financial, rights={allowed}', flush=True)
    unique, duplicate = exact_dedup(financial)
    permitted = [r for r in unique if r['modeling_allowed']]
    # Never export rights-held message bodies, even defanged. Their origins and
    # cryptographic duplicate witnesses remain in metadata diagnostics.
    for row in permitted:
        row.pop('text')
        row['validated_label']='uncertain'; row['message_function']='pending_semantic_review'
    save_csv(DATA/'candidates/permitted_financial_candidates.csv', permitted)
    save_csv(RESULTS/'diagnostics/exact_duplicates.csv', duplicate, ['representative_id','duplicate_id','source_id','original_normalized_sha256'])
    save_csv(RESULTS/'diagnostics/source_counts.csv', audit)
    sting = json.loads((RESULTS/'sting9_status.json').read_text())
    registry.append({'source_id':'sting9', 'aggregator':'none', 'original_dataset':'Sting9', 'original_url':'https://sting9.org/dataset',
          'retrieved_from':'https://api.sting9.org/api/v1/export', 'retrieval_date':when, 'source_version':'not_acquired',
          'commit_sha':'', 'file_sha256':'', 'channel':'mixed', 'language':'mixed', 'original_label_schema':'unavailable',
          'candidate_label_mapping':'verified and semantic review required; confidence_score never ground truth',
          'license_text':'Dataset/Swagger CC0; homepage/terms ODC-BY-NC with clarifications', 'license_status':'CONFLICTING',
          'redistribution_allowed':False, 'notes':'HTTP401 export/submissions; official dump HTTP404; no records acquired'})
    save_csv(DATA/'provenance/source_registry.csv', registry)
    save_json(stamp_path, {'repository_url':'https://github.com/MarazMia/SMISH_DT', 'commit_sha':revision,
        'retrieval_timestamp_utc':when, 'method':'git clone; required non-LFS SMS files verified against pinned Git objects; unrelated email LFS transfer interrupted',
        'source_files_unmodified':True, 'files':file_ledger,
        'excluded_primary_paths':['ENRON Spam Dataset','KOR_smishing_data_raw','Bangla collections','british-english-sms-corpora.doc','revisedindiandataset.xls'],
        'exclusion_note':'Non-SMS/non-English/unsupported source schema or unresolved original license; not silently pooled'})
    summary = {'raw_source_rows':sum(r['raw_rows'] for r in audit), 'sources_downloaded':len(audit),
        'english_SMS_candidates':sum(r['english_SMS_candidates'] for r in audit),
        'financial_candidates_all_rights':len(financial), 'exact_duplicate_excess_all_rights':len(duplicate),
        'unique_financial_messages_all_rights':len(unique), 'permitted_unique_financial_candidates':len(permitted),
        'permitted_candidate_source_counts':dict(Counter(r['source_id'] for r in permitted)),
        'reviewed_messages':0, 'final_independent_messages':0, 'license_note':'Parsing/keywords do not approve source truth or modeling labels',
        'sting9_records':0}
    save_json(RESULTS/'acquisition_summary.json', summary)
    print(json.dumps(summary, indent=2))


if __name__=='__main__': main()
