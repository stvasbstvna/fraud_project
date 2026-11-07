"""Separate machine-review freeze validation; never changes human-review gates."""
import pandas as pd
from .automated_review import rewrite_errors


def validate_automated_matrix(data):
    if data.empty:raise ValueError('No automated complete cases')
    required={'frame_id','variant_id','condition','review_mode','automated_source_approved','automated_rewrite_approved',
              'true_label','defanged_text','variant_text','entity','intent','requested_action','destination','source_id','template_family_id'}
    if required-set(data):raise ValueError('Missing automated frozen columns')
    if not data.review_mode.eq('automated').all():raise ValueError('Wrong validation mode')
    yes=lambda s:s.astype(str).str.lower().eq('true').all()
    if not yes(data.automated_source_approved) or not yes(data.automated_rewrite_approved):raise ValueError('Pending/rejected machine review')
    if data.variant_id.duplicated().any():raise ValueError('Duplicate variants')
    invariants=['true_label','defanged_text','entity','intent','requested_action','destination','source_id','template_family_id']
    for fid,g in data.groupby('frame_id'):
        if len(g)!=7 or set(g.condition)!={f'C{i}' for i in range(7)}:raise ValueError('Incomplete C0–C6 case')
        if any(g[k].nunique(dropna=False)!=1 for k in invariants):raise ValueError('Controlled semantics changed')
        for r in g.to_dict('records'):
            if rewrite_errors(r):raise ValueError('Unsafe or changed frozen variant')
            if r['condition']!='C0' and not all(r.get(k) for k in ['generation_request_hash','rewrite_A_hash','rewrite_B_hash']):raise ValueError('Missing generation/review evidence')
    anchors=data[data.condition.eq('C0')]
    if not anchors.template_family_id.is_unique:raise ValueError('Repeated template family')
    labels=anchors.true_label.value_counts()
    if set(labels.index)!={'phishing_scam','legitimate'} or labels.nunique()!=1:raise ValueError('Unbalanced complete cases')
    if anchors.source_id.value_counts().max()>len(anchors)/2:raise ValueError('Source dominates cohort')


def run_freeze(config,client):
    import hashlib,json
    from datetime import datetime,timezone
    import joblib
    from .core import ROOT,DATA,CONFIG,write_json
    from .automated_io import write_csv
    from .automated_protocol import AUTO_DATA,AUTO_RESULTS,PAIR_PROMPT,PAIR_SCHEMA
    from .automated_runtime import concurrent_map
    from .freeze_benchmark import model_records
    from .measure_distances import measure
    path=DATA/'frozen/automated_pilot_frozen.csv';mpath=DATA/'frozen/automated_pilot_manifest.json'
    if path.exists() and mpath.exists():return pd.read_csv(path,keep_default_na=False),json.loads(mpath.read_text())
    data=pd.read_csv(AUTO_DATA/'complete_balanced_matrix.csv',keep_default_na=False)
    if data.empty:
        write_json(AUTO_RESULTS/'freeze_status.json',{'status':'NO_COMPLETE_BALANCED_CASES','review_mode':'automated','frozen_rows':0})
        return data,{'status':'NO_COMPLETE_BALANCED_CASES','rows':0,'frames':0}
    validate_automated_matrix(data)
    source=pd.read_csv(DATA/'source/automated_source_cohort.csv',keep_default_na=False).set_index('frame_id')
    fixed=['true_label','intent','requested_action','entity','destination','source_id','template_family_id']
    evidence={}
    for row in data.to_dict('records'):
        from .automated_evidence import verify_variant_approval
        verify_variant_approval(row,config)
        anchor=source.loc[row['frame_id']]
        if row['defanged_text']!=anchor.safe_text or any(str(row[k])!=str(anchor[k]) for k in fixed):raise ValueError('Source cohort binding changed')
        for key in ['source_review_A_hash','source_review_B_hash','source_adjudication_hash','generation_request_hash','rewrite_A_hash','rewrite_B_hash','rewrite_adjudication_hash']:
            hashed=row.get(key,'')
            if not hashed:continue
            p=AUTO_DATA/'calls'/f'{hashed}.result.json';q=AUTO_DATA/'calls'/f'{hashed}.request.json'
            result=json.loads(p.read_text(encoding='utf-8'));request=json.loads(q.read_text(encoding='utf-8'))
            if result['status']!='completed' or result['request_hash']!=hashed or request['request_hash']!=hashed:raise ValueError('Missing actual provider evidence')
            if result['model']!=config['roles'][result['role']]:raise ValueError('Machine model substituted')
            if key=='generation_request_hash':
                if result['role']!='generator' or result['output']['text']!=row['variant_text']:raise ValueError('Raw generation text changed')
                if result['prompt_sha256']!=config['generation_prompt_hashes'][row['condition']]:raise ValueError('Generation prompt mismatch')
            for file in [p,q]:evidence[file.relative_to(ROOT).as_posix()]=hashlib.sha256(file.read_bytes()).hexdigest()
    models=model_records();vectors={}
    for record in models:
        short='lr' if 'logistic' in record['path'] else 'rf';vectors[short]=joblib.load(ROOT/record['path']).named_steps['tfidf']
    data=measure(data,vectors)
    write_csv(AUTO_DATA/'approved_distance_measurements.csv',data.to_dict('records'),list(data.columns))
    wide=data.pivot(index='frame_id',columns='condition',values='surface_distance')
    pairs=[]
    for fid,g in data.groupby('frame_id'):
        g=g.set_index('condition');pairs.append({'frame_id':fid,'requested_action':g.iloc[0].requested_action,
            'original':g.iloc[0].defanged_text,'C2':g.loc['C2','variant_text'],'C3':g.loc['C3','variant_text']})
    def judge_pair(payload):
        a=client.call('llm_reviewer_A',PAIR_PROMPT,payload,PAIR_SCHEMA)
        b=client.call('llm_reviewer_B',PAIR_PROMPT,payload,PAIR_SCHEMA)
        good=lambda x:all(x[k] is True for k in ['same_action','c3_less_direct','safe']) and x['confidence']>=config['confidence_threshold']
        return {'frame_id':payload['frame_id'],'review_A_hash':a['request_hash'],'review_B_hash':b['request_hash'],
                'C3_less_direct_both':good(a['output']) and good(b['output'])}
    direct=concurrent_map(judge_pair,pairs,config['max_workers'])
    write_csv(AUTO_RESULTS/'directness_pair_review.csv',direct,list(direct[0]))
    thresholds=config['manipulation_thresholds']
    manipulation={'review_mode':'automated','frames':len(wide),'C1_lower_C5_fraction':float((wide.C1<wide.C5).mean()),
        'C1_lower_C6_fraction':float((wide.C1<wide.C6).mean()),'C3_less_direct_fraction':sum(r['C3_less_direct_both'] for r in direct)/len(direct)}
    manipulation['passed']=all(manipulation[k]>=thresholds[k] for k in thresholds)
    write_json(AUTO_RESULTS/'manipulation_check.json',manipulation)
    write_csv(path,data.to_dict('records'),list(data.columns))
    anchors=data[data.condition.eq('C0')]
    config_path=CONFIG/'automated_pilot/protocol.json'
    files=[config_path,CONFIG/'source_registry.csv',DATA/'source/automated_source_cohort.csv',
        DATA/'review/automated_source_review.csv',DATA/'review/automated_source_decisions.csv',
        DATA/'review/automated_rewrite_review.csv',DATA/'review/automated_adjudication.csv',
        *[CONFIG/'prompts'/p for p in config['generation_prompt_files'].values()],
        *sorted((CONFIG/'automated_pilot').glob('*.txt'))]
    manifest={'status':'FROZEN_AUTOMATED','review_mode':'automated','validation_type':'automated_semantic_review',
        'frames':len(anchors),'rows':len(data),'condition_count':7,'label_balance':anchors.true_label.value_counts().to_dict(),
        'source_distribution':anchors.source_id.value_counts().to_dict(),'template_families':int(anchors.template_family_id.nunique()),
        'data_sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'timestamp_utc':datetime.now(timezone.utc).isoformat(),
        'models':models,'review_models':config['roles'],'manipulation':manipulation,'detector_feedback_used':False,
        'independent_human_annotation':False,'inference_scope':'exploratory_reduced_machine_reviewed_pilot',
        'generation_closed_before_scoring':True,
        'artifact_hashes':{p.relative_to(ROOT).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in files},
        'provider_evidence_hashes':evidence}
    write_json(mpath,manifest);print(f'FROZEN AUTOMATED: {len(anchors)} frames, {len(data)} rows; manipulation passed={manipulation["passed"]}',flush=True)
    return data,manifest


def run_evaluation(config):
    import hashlib,json
    import numpy as np
    import joblib
    from .core import ROOT,DATA,write_json
    from .automated_io import write_csv
    from .automated_protocol import AUTO_RESULTS
    from .freeze_benchmark import model_records
    output=DATA/'evaluation/automated_pilot_predictions.csv'
    manifest_path=DATA/'frozen/automated_pilot_manifest.json'
    manifest=json.loads(manifest_path.read_text(encoding='utf-8'));path=DATA/'frozen/automated_pilot_frozen.csv'
    if manifest['status']!='FROZEN_AUTOMATED' or manifest['validation_type']!='automated_semantic_review':raise ValueError('Wrong freeze type')
    if hashlib.sha256(path.read_bytes()).hexdigest()!=manifest['data_sha256']:raise ValueError('Frozen pilot changed')
    for rel,expected in {**manifest['artifact_hashes'],**manifest['provider_evidence_hashes']}.items():
        if hashlib.sha256((ROOT/rel).read_bytes()).hexdigest()!=expected:raise ValueError('Frozen evidence changed: '+rel)
    if model_records()!=manifest['models']:raise ValueError('Historical detector changed')
    data=pd.read_csv(path,keep_default_na=False);validate_automated_matrix(data)
    from .automated_evidence import verify_variant_approval,load_prediction_cache
    for row in data.to_dict('records'):verify_variant_approval(row,config)
    if output.exists():
        return load_prediction_cache(output,AUTO_RESULTS/'evaluation_manifest.json',manifest['data_sha256'],manifest['models'])
    for short in ['lr','rf']:
        record=next(r for r in manifest['models'] if ('logistic' if short=='lr' else 'random_forest') in r['path'])
        pipeline=joblib.load(ROOT/record['path']);classes=list(pipeline.classes_)
        data[f'{short}_probability']=pipeline.predict_proba(data.variant_text)[:,classes.index(1)]
        data[f'{short}_prediction']=pipeline.predict(data.variant_text)
        values=data[f'{short}_probability']
        if not np.isfinite(values).all() or not values.between(0,1).all():raise ValueError('Invalid probabilities')
        baseline=data[data.condition.eq('C0')].set_index('frame_id')[f'{short}_probability']
        data[f'{short}_delta']=data.frame_id.map(baseline)-values
    write_csv(output,data.to_dict('records'),list(data.columns))
    write_json(AUTO_RESULTS/'evaluation_manifest.json',{'status':'EVALUATED','review_mode':'automated','frozen_rows':len(data),
        'frozen_data_sha256':manifest['data_sha256'],'predictions_sha256':hashlib.sha256(output.read_bytes()).hexdigest(),
        'models':manifest['models'],'threshold':.5,'fit_calls':0})
    print(f'Evaluated {len(data)} frozen rows with unchanged LR/RF, no fitting',flush=True)
    return data
