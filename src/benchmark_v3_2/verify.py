"""Reconstruct actual provider approvals and frozen score/evidence bindings."""
from .core import *
from .calls import verify_record
from .sources import validate_packet,source_consensus,family_filter
from .generate import deterministic_errors,verify_prefreeze

META={'evidence_request_sha256','review_model','review_prompt_version','review_timestamp'}

def verify_sources():
    packet=read(DATA/'source/outbound_packet.json')+read(DATA/'source/additional_outbound_packet.json')
    lookup=validate_packet(packet,csv_rows(DATA/'source/review_candidates.csv')+csv_rows(DATA/'source/additional_candidates.csv'))
    decisions=read(DATA/'review/final_source_decisions.json')
    if len(decisions)!=len(packet) or {d['frame_id'] for d in decisions}!={r['id'] for r in packet}:raise ValueError('Source coverage')
    approved={}
    for d in decisions:
        a,b,j=d['A'],d['B'],d['J'];ident=d['frame_id']
        consensus=bool(a and b and source_consensus(a,b));annotation=a if consensus else j
        ok=bool(a and b and approved_source(annotation) and (consensus or j))
        if ok!=d['approved'] or d['annotation']!=(annotation if ok else None):raise ValueError('Source decision reconstruction')
        for role,assessment in [('A',a),('B',b),('J',j)]:
            if not assessment:continue
            results,request=bound_call('source_review',role,assessment['evidence_request_sha256'])
            item=next(r for r in results if r['id']==ident)
            supplied=next(r for r in json.loads(request['request_payload']['input'])['items'] if r['id']==ident)
            expected=next(r for r in packet if r['id']==ident)
            if any(supplied.get(k)!=v for k,v in expected.items()) or item!={k:v for k,v in assessment.items() if k not in META}:raise ValueError('Source provider/text binding')
            if item['frame_id']!=ident:raise ValueError('Source frame_id differs from id')
            if role=='J' and (supplied['review_A']!=a or supplied['review_B']!=b):raise ValueError('Source adjudication chain')
        if ok:approved[ident]=annotation
    sources=csv_rows(DATA/'frozen/source_cohort.csv')
    for r in sources:
        if r['frame_id'] not in approved or sha(r['safe_text'])!=r['source_text_sha256']:raise ValueError('C0 unapproved/hash')
        original=lookup[r['frame_id']];annotation=approved[r['frame_id']]
        if original['safe_text']!=r['safe_text'] or original['source_id']!=r['source_dataset'] or annotation['label']!=r['validated_label'] or int(r['true_label'])!=int(annotation['label']=='phishing'):raise ValueError('Approved C0 binding')
        for k in ['intent','requested_action','institution_entity','destination','message_function','event_or_claim']:
            if r[k]!=annotation[k]:raise ValueError('Source control mismatch')
    old=csv_rows(ROOT/'data/benchmark_v3/final_run/frozen/modeling_cohort.csv')
    reference=[r for r in old if r['split']!='held_out_test']
    compatible=[dict(r,id=r['frame_id'],source_id=r['source_dataset']) for r in sources]
    kept,_,_=family_filter(compatible,reference)
    if len(kept)!=len(sources):raise ValueError('Final training/template overlap or withincohort duplicate')
    return sources

_CALLS={}
def bound_call(phase,role,h):
    key=(phase,role,h)
    if key not in _CALLS:
        base=DATA/('generated/calls' if role=='G' else f'review/{phase}/calls')
        path=base/f'{role}_{h}.response.json'
        if not path.exists() and phase=='source_review':path=DATA/f'review/source_review/recovery_calls/{role}_{h}.response.json'
        items,req=verify_record(path)
        if req['role']!=role or req['phase']!=phase or req['request_payload']['model']!=ROLES[role]:raise ValueError('Role/snapshot mismatch')
        blind(json.loads(req['request_payload']['input']))
        _CALLS[key]=(items,req)
    return _CALLS[key]

def verify_matrix():
    verify_prefreeze();sources=verify_sources();lookup={s['frame_id']:s for s in sources}
    manifest=read(DATA/'frozen/matrix_manifest.json');rows=csv_rows(DATA/'frozen/robustness_matrix.csv')
    if file_sha(DATA/'frozen/robustness_matrix.csv')!=manifest['matrix_sha256'] or file_sha(DATA/'review/rewrite_decisions.json')!=manifest['decisions_sha256']:raise ValueError('Frozen matrix evidence changed')
    decisions=read(DATA/'review/rewrite_decisions.json');bykey={d['id']:d for d in decisions}
    attempts=defaultdict(list)
    for d in decisions:
        attempts[d['frame_id'],d['condition']].append(d)
        answer=d['generation']
        if answer:
            out,req=bound_call('generation','G',answer['evidence_request_sha256'])
            item=next(r for r in out if r['id']==d['id'])
            inp=next(r for r in json.loads(req['request_payload']['input'])['items'] if r['id']==d['id'])
            if item['text']!=answer['text'] or inp['source']!=lookup[d['frame_id']]['safe_text'] or inp['attempt']!=d['attempt'] or inp['condition']!=d['condition']:raise ValueError('Generator evidence')
        for role in ['A','B','J']:
            assessment=d.get(role)
            if not assessment:continue
            out,req=bound_call('rewrite_review',role,assessment['evidence_request_sha256'])
            item=next(r for r in out if r['id']==d['id']);inp=next(r for r in json.loads(req['request_payload']['input'])['items'] if r['id']==d['id'])
            if item!={k:v for k,v in assessment.items() if k not in META} or inp['source']!=d['source'] or inp['text']!=answer['text']:raise ValueError('Rewrite review exact binding')
            if role=='J' and (inp['review_A']!=d['A'] or inp['review_B']!=d['B']):raise ValueError('Rewrite adjudication chain')
        a,b,j=d.get('A'),d.get('B'),d.get('J')
        agree=bool(a and b and all(a[k]==b[k] for k in GATES))
        semantic=bool(a and b and ((agree and approved_rewrite(a) and approved_rewrite(b)) or (not agree and approved_rewrite(j))))
        errors=deterministic_errors(d,answer)
        if errors!=d['deterministic_errors'] or d['approved']!=(not errors and semantic):raise ValueError('Rewrite approval reconstruction')
    for key,group in attempts.items():
        if len(group)>2 or {g['attempt'] for g in group} not in [{0},{0,1}]:raise ValueError('Retry limit')
        if len(group)==2:
            initial=next(g for g in group if g['attempt']==0)
            if not retry_allowed(0,initial['deterministic_errors']):raise ValueError('Unpermitted retry')
    complete=complete_ids(rows)
    for r in rows:
        source=lookup[r['frame_id']]
        if r['true_label']!=source['true_label'] or sha(r['text'])!=r['text_sha256'] or (r['primary_complete_case']=='True')!=(r['frame_id'] in complete):raise ValueError('Matrix label/hash/completeness')
        if r['condition']=='C0':
            if r['text']!=source['safe_text']:raise ValueError('C0 changed')
        else:
            d=bykey[r['frame_id']+'::'+r['condition']+'::'+r['attempt']]
            if not d['approved'] or r['text']!=d['generation']['text']:raise ValueError('Unapproved frozen rewrite')
    if sum(r['condition']=='C0' for r in rows)!=len(sources):raise ValueError('Missing C0')
    return rows,sources

def verify():
    rows,sources=verify_matrix();keys={(r['frame_id'],r['condition']):r for r in rows}
    predmanifest=read(RESULTS/'predictions/prediction_manifest.json')
    models={m['model_name']:m for m in read(MODELS/'MODEL_FREEZE_MANIFEST.json')['models']}
    for name,h in predmanifest['files'].items():
        path=RESULTS/f'predictions/{name}_predictions.csv'
        if file_sha(path)!=h:raise ValueError('Prediction cache hash')
        predictions=csv_rows(path)
        if len(predictions)!=len(keys) or {(r['frame_id'],r['condition']) for r in predictions}!=set(keys):raise ValueError('Prediction coverage')
        for r in predictions:
            if int(r['prediction'])!=int(float(r['probability'])>=.5) or abs(float(r['signed_delta'])-(float(r['C0_probability'])-float(r['probability'])))>1e-12 or abs(float(r['absolute_delta'])-abs(float(r['signed_delta'])))>1e-12:raise ValueError('Probability/pair consistency')
        anchors={r['frame_id']:r for r in predictions if r['condition']=='C0'}
        for r in predictions:
            if float(r['C0_probability'])!=float(anchors[r['frame_id']]['probability']) or r['model_sha256']!=models[name]['sha256'] or r['text_sha256']!=keys[r['frame_id'],r['condition']]['text_sha256']:raise ValueError('Model/C0/text prediction binding')
        if name in {'LR','RF'}:
            import joblib
            from src.benchmark_v3.baselines import probabilities
            values=probabilities(joblib.load(ROOT/models[name]['model_path']),[keys[r['frame_id'],r['condition']]['text'] for r in predictions])
            if any(abs(float(r['probability'])-p)>1e-12 for r,p in zip(predictions,values)):raise ValueError('Lexical numerical reproduction mismatch')
    replay=read(RESULTS/'predictions/modernbert_replay.json')
    if replay['model_sha256']!=models['ModernBERT']['sha256'] or replay['matrix_sha256']!=file_sha(DATA/'frozen/robustness_matrix.csv') or replay['max_absolute_difference']>1e-7:raise ValueError('Modern replay mismatch')
    figures=list((RESULTS/'figures').glob('*_metadata.json'))
    for f in figures:
        metadata=read(f)
        if not all(k in metadata for k in ['title','N','source_data','filters','main_observation','allowed_interpretation','forbidden_interpretation']):raise ValueError('Figure metadata')
        for p in metadata['source_data']:
            if not (ROOT/p).exists():raise ValueError('Missing figure source: '+p)
        if not f.with_name(f.name.replace('_metadata.json','_data.csv')).is_file():raise ValueError('Missing figure exact data')
    inventory=verify_protected()
    receipt={'status':'VERIFIED_EXPLORATORY_V32','protected_prior_files':inventory,'protected_files_changed':0,'source_frames':len(sources),'source_labels':dict(Counter(s['validated_label'] for s in sources)),'approved_variants':sum(r['condition']!='C0' for r in rows),'complete_frames':len(complete_ids(rows)),'all_approved_raw_provider_evidence_reconstructed':True,'no_detector_feedback':True,'family_training_validation_overlap':False,'model_freeze_verified':True,'figures':len(figures),'matrix_sha256':file_sha(DATA/'frozen/robustness_matrix.csv'),'primary_stronger_pilot_target_met':all(sum(s['validated_label']==label and s['frame_id'] in complete_ids(rows) for s in sources)>=30 for label in ['phishing','legitimate'])}
    immutable_json(RESULTS/'verification.json',receipt)
    print(json.dumps(receipt,indent=2),flush=True)
    return receipt

if __name__=='__main__':verify()
