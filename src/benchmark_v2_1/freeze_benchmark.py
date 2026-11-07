"""Freeze only complete, reviewed sets; pending output contains headers and no data rows."""
import argparse
import json
from pathlib import Path
import hashlib
import pandas as pd
from .core import ROOT, DATA, CONFIG, RESULTS, VARIANT_FIELDS, FRAME_FIELDS, INVARIANTS, freeze_rows, source_eligible, verify_source_reviews, digest, write_csv, write_json


def model_records():
    expected=pd.read_csv(ROOT/'results/rewrite_experiment/model_hashes.csv')
    records=[]
    for r in expected.to_dict('records'):
        path=ROOT/r['model_file']; observed=hashlib.sha256(path.read_bytes()).hexdigest()
        if observed!=r['sha256']:raise ValueError(f'Frozen model changed: {path}')
        records.append({'path':r['model_file'],'sha256':observed})
    return records


def verify_source_binding(rows,source):
    for r in rows:
        expected=source[r['frame_id']]
        if not source_eligible(expected):raise ValueError('Canonical source remains quarantined')
        if any(str(r[k])!=str(expected[k]) for k in FRAME_FIELDS if k!='notes'):
            raise ValueError('Source metadata changed in variant matrix')


def verify_manipulation_binding(manipulation,input_sha256):
    if manipulation.get('input_sha256')!=input_sha256:raise ValueError('Manipulation validation belongs to different matrix')
    if manipulation.get('models')!=model_records():raise ValueError('Manipulation representation changed')
    if not all(manipulation.get(k) is True for k in ['C1_lower_than_C5','C1_lower_than_C6']):
        raise ValueError('Condition-distance manipulation validation pending or failed')


def main():
    p=argparse.ArgumentParser();p.add_argument('--input',type=Path,default=DATA/'generated/variant_matrix.csv')
    p.add_argument('--reviews',type=Path,default=DATA/'review/review_queue.csv')
    p.add_argument('--frames',type=Path,default=DATA/'source/frames.csv')
    p.add_argument('--source-reviews',type=Path,default=DATA/'review/source_review_completed.csv')
    p.add_argument('--responses',type=Path,help='Retained raw response JSONL evidence')
    p.add_argument('--pending',action='store_true');a=p.parse_args()
    frames=pd.read_csv(a.frames,keep_default_na=False)
    rows=pd.read_csv(a.input,keep_default_na=False).to_dict('records')
    rv=pd.read_csv(a.reviews,keep_default_na=False).to_dict('records')
    frozen=[];status='PENDING'
    if not a.pending:
        manipulation=json.loads((RESULTS/'diagnostics/manipulation_check.json').read_text(encoding='utf-8'))
        verify_manipulation_binding(manipulation,hashlib.sha256(a.input.read_bytes()).hexdigest())
        pilot=json.loads((DATA/'review/pilot_validation.json').read_text(encoding='utf-8'))
        if not all(pilot.get(k) is True for k in ['semantic_action_valid','directness_valid','agreement_adjudicated','attrition_rule_frozen']):
            raise ValueError('Independent pilot validation pending or failed')
        if pilot.get('review_file_sha256')!=hashlib.sha256(a.reviews.read_bytes()).hexdigest():
            raise ValueError('Pilot review evidence changed')
        source={r['frame_id']:r for r in frames.to_dict('records')}
        verify_source_binding(rows,source)
        source_reviews=pd.read_csv(a.source_reviews,keep_default_na=False).to_dict('records')
        selected=frames[frames.frame_id.isin({r['frame_id'] for r in rows})]
        verify_source_reviews(selected.to_dict('records'),source_reviews)
        from .generate_variants import make_requests,verify_response
        requests={r['variant_id']:r for r in make_requests(selected,source_reviews)}
        if not a.responses:raise ValueError('Retained generation responses required')
        envelopes={}
        for line in a.responses.read_text(encoding='utf-8').splitlines():
            envelope=json.loads(line);key=envelope['request_sha256']
            if key in envelopes:raise ValueError('Duplicate raw response request')
            envelopes[key]=envelope
        config=json.loads((CONFIG/'generator_config.json').read_text(encoding='utf-8'))
        for row in rows:
            if row['condition']!='C0':
                req=requests[row['variant_id']]
                verify_response(row,req,envelopes.get(req['request_sha256'],{}),config)
        frozen=freeze_rows(rows,rv);status='FROZEN'
    config_paths=[CONFIG/'generator_config.json',CONFIG/'benchmark_config.yaml',*sorted((CONFIG/'prompts').glob('*.txt'))]
    manifest={'status':status,'rows':len(frozen),'frames':len({r['frame_id'] for r in frozen}),
              'candidate_frames':len(frames),'eligible_sources':sum(source_eligible(r) for r in frames.to_dict('records')),
              'models':model_records(),'config_hashes':{p.relative_to(ROOT).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in config_paths},
              'blockers':[] if frozen else ['source_semantic_review','generation','independent_variant_reviews','pilot_manipulation_validation']}
    manifest['review_file_sha256']=hashlib.sha256(a.reviews.read_bytes()).hexdigest()
    manifest['source_file_sha256']=hashlib.sha256(a.frames.read_bytes()).hexdigest()
    if not a.pending:
        manifest['source_review_file_sha256']=hashlib.sha256(a.source_reviews.read_bytes()).hexdigest()
        manifest['raw_response_file_sha256']=hashlib.sha256(a.responses.read_bytes()).hexdigest()
    path=DATA/'frozen/benchmark_v2_1.csv';write_csv(path,frozen,VARIANT_FIELDS)
    manifest['dataset_sha256']=hashlib.sha256(path.read_bytes()).hexdigest()
    write_json(DATA/'frozen/manifest.json',manifest)
    print(f'{status}: {len(frozen)} frozen rows')


if __name__=='__main__':main()
