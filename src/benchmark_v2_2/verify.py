"""Read-only integrity checks and an additive verification receipt."""
import csv
import json
import pandas as pd
from .source_audit import ROOT, DATA, RESULTS, sha, save_json, capacity_bound


def verify_baseline(root, inventory):
    records = list(csv.DictReader(inventory.open(encoding='utf-8')))
    for row in records:
        path = root / row['path']
        if not path.is_file() or sha(path.read_bytes()) != row['sha256']:
            raise ValueError(f'Changed or missing historical evidence: {row["path"]}')
    return len(records)


def verify():
    checked = verify_baseline(ROOT, ROOT / 'docs/benchmark_v2_2/BASELINE_INVENTORY.csv')
    summary = json.loads((RESULTS / 'source_summary.json').read_text())
    manifest = json.loads((DATA / 'frozen/source_cohort_manifest.json').read_text())
    audit = DATA / 'source/candidate_audit.csv'
    if sha(audit.read_bytes()) != summary['source_candidate_audit_sha256'] or manifest['source_audit_sha256'] != summary['source_candidate_audit_sha256']:
        raise ValueError('Source audit hash mismatch')
    rows = pd.read_csv(audit, keep_default_na=False, low_memory=False).to_dict('records')
    if capacity_bound(rows) != summary['capacity_bound']:
        raise ValueError('Source capacity does not reproduce')
    if summary['status'] != 'V2.2 SOURCE COHORT INSUFFICIENT' or summary['capacity_bound']['source_capacity_sufficient']:
        raise ValueError('Unexpected source feasibility status')
    cohort = DATA / 'frozen/source_cohort.csv'
    if sha(cohort.read_bytes()) != manifest['source_cohort_sha256'] or len(pd.read_csv(cohort)) != 0 or manifest['status'] != 'NOT_FROZEN_SOURCE_COHORT_INSUFFICIENT':
        raise ValueError('Failed source cohort must remain empty and NOT FROZEN')
    models = {'models/final/tfidf_logistic_regression.joblib': '84ba84863ce9a8fd757cd4e9babc6dacf39496223299a06df0054f94ca688fcc',
              'models/final/tfidf_random_forest.joblib': '99c4a06e7ad52ff000c0a1d8818ca61cdc268d929a1a970e79d74b6e0c38b4fc'}
    for name, expected in models.items():
        if sha((ROOT / name).read_bytes()) != expected:
            raise ValueError('Historical model hash mismatch')
    for name, expected in {'mendeley_sms_v1.zip': '9bbf3188fdad81495d8e82825648b9b63b53fc86841a3d26c02629990b233cc3',
                           'uci_sms.zip': '1587ea43e58e82b14ff1f5425c88e17f8496bfcdb67a583dbff9eefaf9963ce3',
                           'gateway_phishing.csv': 'd125c394af792faeb2b71b3f7100cad3b4cece02aff78cb4ec1fb9e7db90f230',
                           'financial_scams_v2.csv': '58ec802e4de8768643e3be0badbaedb3ae5017a273e8f3898e72f6a29cbc96ad'}.items():
        if sha((DATA / 'source_snapshots' / name).read_bytes()) != expected:
            raise ValueError('Original snapshot hash mismatch')
    if any(DATA.rglob('*.result.json')) or (DATA / 'evaluation').exists():
        raise ValueError('Unexpected downstream output after source stop')
    result = {'status': 'VERIFIED_SOURCE_INSUFFICIENT_NO_DOWNSTREAM_EXECUTION', 'historical_files_checked': checked,
              'historical_files_changed': 0, 'original_local_rows_inspected': summary['input_rows_inspected'],
              'optimistic_max_controls': summary['capacity_bound']['maximum_legitimate_before_semantic_review'],
              'required_controls': 16, 'final_source_frames': 0, 'LLM_calls': 0, 'generated_variants': 0,
              'detector_predictions': 0, 'scientific_figures': 0, 'models_unchanged': True,
              'review_type': 'deterministic_source_audit_only', 'independent_human_annotation': False}
    save_json(RESULTS / 'verification.json', result)
    return result


if __name__ == '__main__':
    print(json.dumps(verify(), indent=2))
