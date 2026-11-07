"""Explicit exploratory incomplete-case freeze; never claims a complete primary pilot."""
from __future__ import annotations
import hashlib
import json
from datetime import datetime,timezone
import numpy as np
import pandas as pd
import joblib
from .core import ROOT,DATA,CONFIG,write_json
from .automated_io import write_csv
from .automated_protocol import AUTO_DATA,AUTO_RESULTS
from .automated_review import rewrite_errors
from .freeze_benchmark import model_records
from .measure_distances import measure


def validate_available(data):
    required={'frame_id','variant_id','condition','review_mode','automated_source_approved','automated_rewrite_approved',
        'true_label','defanged_text','variant_text','entity','intent','requested_action','destination','source_id','template_family_id'}
    if data.empty or required-set(data):raise ValueError('Missing available-pair data')
    if not data.review_mode.eq('automated').all():raise ValueError('Wrong review mode')
    for field in ['automated_source_approved','automated_rewrite_approved']:
        if not data[field].astype(str).str.lower().eq('true').all():raise ValueError('Unapproved machine-review row')
    if data.variant_id.duplicated().any() or data.duplicated(['frame_id','condition']).any():raise ValueError('Duplicate available condition')
    for fid,g in data.groupby('frame_id'):
        if not set(g.condition).issubset({f'C{i}' for i in range(7)}) or g.condition.eq('C0').sum()!=1:raise ValueError('Missing unique source baseline')
        if any(g[k].nunique(dropna=False)!=1 for k in ['true_label','defanged_text','entity','intent','requested_action','destination','source_id','template_family_id']):raise ValueError('Changed controlled semantics')
        for r in g.to_dict('records'):
            if rewrite_errors(r):raise ValueError('Invalid available variant')
            if r['condition']!='C0' and not all(r.get(k) for k in ['generation_request_hash','rewrite_A_hash','rewrite_B_hash']):raise ValueError('Missing machine evidence hashes')
    anchors=data[data.condition.eq('C0')]
    if not anchors.template_family_id.is_unique:raise ValueError('Repeated source family')


def freeze_available(config):
    path=DATA/'frozen/automated_available_pairs_exploratory.csv'
    mpath=DATA/'frozen/automated_available_pairs_manifest.json'
    if path.exists() and mpath.exists():return pd.read_csv(path,keep_default_na=False),json.loads(mpath.read_text())
    reviewed=pd.read_csv(AUTO_DATA/'reviewed_matrix.csv',keep_default_na=False)
    data=reviewed[reviewed.automated_rewrite_approved.astype(str).str.lower().eq('true')].copy()
    validate_available(data)
    source=pd.read_csv(DATA/'source/automated_source_cohort.csv',keep_default_na=False).set_index('frame_id')
    evidence={}
    for row in data.to_dict('records'):
        from .automated_evidence import verify_variant_approval
        verify_variant_approval(row,config)
        anchor=source.loc[row['frame_id']]
        if row['defanged_text']!=anchor.safe_text or any(str(row[k])!=str(anchor[k]) for k in ['true_label','entity','intent','requested_action','destination','source_id','template_family_id']):raise ValueError('Source binding changed')
        for name in ['source_review_A_hash','source_review_B_hash','source_adjudication_hash','generation_request_hash','rewrite_A_hash','rewrite_B_hash','rewrite_adjudication_hash']:
            key=row.get(name,'')
            if not key:continue
            request=AUTO_DATA/'calls'/f'{key}.request.json';result=AUTO_DATA/'calls'/f'{key}.result.json'
            req=json.loads(request.read_text());resp=json.loads(result.read_text())
            if resp['status']!='completed' or resp['request_hash']!=key or req['request_hash']!=key:raise ValueError('Incomplete actual provider evidence')
            if resp['model']!=config['roles'][resp['role']]:raise ValueError('Model substituted')
            if name=='generation_request_hash':
                if resp['role']!='generator' or resp['output']['text']!=row['variant_text']:raise ValueError('Changed generated text')
                if resp['prompt_sha256']!=config['generation_prompt_hashes'][row['condition']]:raise ValueError('Generation prompt changed')
            for file in [request,result]:evidence[file.relative_to(ROOT).as_posix()]=hashlib.sha256(file.read_bytes()).hexdigest()
    models=model_records();vectors={}
    for model in models:
        vectors['lr' if 'logistic' in model['path'] else 'rf']=joblib.load(ROOT/model['path']).named_steps['tfidf']
    data=measure(data,vectors);write_csv(path,data.to_dict('records'),list(data.columns))
    primary=DATA/'frozen/automated_pilot_frozen.csv'
    write_csv(primary,[],list(data.columns))
    primary_manifest={'status':'NOT_FROZEN_NO_COMPLETE_CASES','validation_type':'automated_semantic_review','review_mode':'automated',
        'frames':0,'rows':0,'reason':'All four sources lack at least one approved C1–C6 condition',
        'header_only_sha256':hashlib.sha256(primary.read_bytes()).hexdigest()}
    write_json(DATA/'frozen/automated_pilot_manifest.json',primary_manifest)
    anchors=data[data.condition.eq('C0')]
    files=[DATA/'source/automated_source_cohort.csv',DATA/'review/automated_source_review.csv',DATA/'review/automated_source_decisions.csv',
        DATA/'review/automated_rewrite_review.csv',DATA/'review/automated_adjudication.csv',CONFIG/'automated_pilot/protocol.json',
        CONFIG/'source_registry.csv',AUTO_DATA/'generated_variants.csv',AUTO_DATA/'reviewed_matrix.csv',
        ROOT/'docs/benchmark_v2_1/AUTOMATED_AVAILABLE_PAIR_ANALYSIS_PLAN.md',
        *[CONFIG/'prompts'/p for p in config['generation_prompt_files'].values()],*sorted((CONFIG/'automated_pilot').glob('*.txt'))]
    manifest={'status':'FROZEN_AUTOMATED_AVAILABLE_PAIRS_EXPLORATORY','review_mode':'automated',
        'validation_type':'automated_semantic_review','independent_human_annotation':False,'complete_C0_C6_frames':0,
        'source_frames':len(anchors),'rows':len(data),'label_balance_at_C0':anchors.true_label.value_counts().to_dict(),
        'condition_counts':data.condition.value_counts().sort_index().to_dict(),'source_distribution':anchors.source_id.value_counts().to_dict(),
        'template_families':int(anchors.template_family_id.nunique()),'models':models,'review_models':config['roles'],
        'data_sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'timestamp_utc':datetime.now(timezone.utc).isoformat(),
        'generation_closed_before_scoring':True,'detector_feedback_used':False,'interpretation':'incomplete_case_exploratory_only',
        'artifact_hashes':{p.relative_to(ROOT).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in files},
        'provider_evidence_hashes':evidence}
    write_json(mpath,manifest)
    print(f'Exploratory available-pair freeze: {len(data)} rows; primary complete cases remain 0',flush=True)
    return data,manifest


def evaluate_available():
    path=DATA/'frozen/automated_available_pairs_exploratory.csv'
    manifest=json.loads((DATA/'frozen/automated_available_pairs_manifest.json').read_text())
    output=DATA/'evaluation/automated_available_pairs_predictions.csv'
    if manifest['status']!='FROZEN_AUTOMATED_AVAILABLE_PAIRS_EXPLORATORY':raise ValueError('Wrong diagnostic freeze')
    if hashlib.sha256(path.read_bytes()).hexdigest()!=manifest['data_sha256']:raise ValueError('Frozen data changed')
    for rel,expected in {**manifest['artifact_hashes'],**manifest['provider_evidence_hashes']}.items():
        if hashlib.sha256((ROOT/rel).read_bytes()).hexdigest()!=expected:raise ValueError('Frozen evidence changed')
    if model_records()!=manifest['models']:raise ValueError('Historical model changed')
    data=pd.read_csv(path,keep_default_na=False);validate_available(data)
    config=json.loads((CONFIG/'automated_pilot/protocol.json').read_text(encoding='utf-8'))
    from .automated_evidence import verify_variant_approval,load_prediction_cache
    for row in data.to_dict('records'):verify_variant_approval(row,config)
    if output.exists():
        return load_prediction_cache(output,AUTO_RESULTS/'available_pair_evaluation_manifest.json',manifest['data_sha256'],manifest['models'])
    for short in ['lr','rf']:
        model=next(r for r in manifest['models'] if ('logistic' if short=='lr' else 'random_forest') in r['path'])
        pipeline=joblib.load(ROOT/model['path']);classes=list(pipeline.classes_)
        data[f'{short}_probability']=pipeline.predict_proba(data.variant_text)[:,classes.index(1)]
        data[f'{short}_prediction']=pipeline.predict(data.variant_text)
        if not np.isfinite(data[f'{short}_probability']).all() or not data[f'{short}_probability'].between(0,1).all():raise ValueError('Invalid probability')
        c0=data[data.condition.eq('C0')].set_index('frame_id')[f'{short}_probability']
        data[f'{short}_delta']=data.frame_id.map(c0)-data[f'{short}_probability']
    write_csv(output,data.to_dict('records'),list(data.columns))
    write_json(AUTO_RESULTS/'available_pair_evaluation_manifest.json',{'status':'EVALUATED_EXPLORATORY_AVAILABLE_PAIRS',
        'review_mode':'automated','rows':len(data),'primary_complete_cases':0,'threshold':.5,'fit_calls':0,
        'frozen_data_sha256':manifest['data_sha256'],'predictions_sha256':hashlib.sha256(output.read_bytes()).hexdigest(),'models':manifest['models']})
    print(f'Local LR/RF evaluated {len(data)} frozen available-pair rows; no fitting',flush=True)
    return data
