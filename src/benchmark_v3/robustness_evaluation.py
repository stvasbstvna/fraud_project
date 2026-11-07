"""Verify a blinded supplemental freeze, then score unchanged primary models."""
import argparse
from collections import Counter,defaultdict
from difflib import SequenceMatcher
import json
import numpy as np
import pandas as pd
import joblib
from sklearn.metrics.pairwise import cosine_similarity
from .core import DATA,MODELS,RESULTS,CONFIG,read_json,digest,file_digest,verify_hash,save_csv,save_json
from .protocol import verify_frozen_inputs
from .baselines import probabilities
from .evaluation import metrics,validate_probability_cache
from .robustness import ROLES,approved,invariant_errors,complete_core


def call(role,key,base=None):
    base=DATA/'robustness' if base is None else base
    matches=list((base/'calls').glob(f'{role}_{key}_*.request.json'))
    if len(matches)!=1:raise ValueError('Ambiguous or missing supplemental provider call')
    request=read_json(matches[0]);raw=request['raw_request']
    if digest(json.dumps(raw,sort_keys=True,ensure_ascii=False))!=key or request['role']!=role or raw['model']!=ROLES[role]:raise ValueError('Supplement request hash/model mismatch')
    response_path=matches[0].with_name(matches[0].name.replace('.request.json','.response.json'))
    response=read_json(response_path);provider=response['raw_response']
    if response['role']!=role or response['model']!=ROLES[role] or provider['model']!=ROLES[role] or provider['status']!='completed':raise ValueError('Supplement provider role/model mismatch')
    if digest(json.dumps(provider,sort_keys=True))!=response['raw_response_sha256']:raise ValueError('Supplement raw response hash mismatch')
    text=''.join(c['text'] for o in provider['output'] for c in o.get('content',[]) if c.get('type')=='output_text')
    items=json.loads(text)['items'];payload=json.loads(raw['input'])['items']
    if sorted(r['id'] for r in items)!=sorted(r['id'] for r in payload):raise ValueError('Supplement exact ID binding failed')
    return {r['id']:r for r in payload},{r['id']:r for r in items}


def verify_supplement():
    freeze=verify_frozen_inputs('primary');base=DATA/'robustness'
    manifest=read_json(base/'freeze_manifest.json');path=base/'frozen_approved_variants.json';verify_hash(path,manifest['frozen_sha256'])
    rows=read_json(path);plan=read_json(CONFIG/'robustness_supplement_plan.json')
    if plan['cohort_sha256']!=freeze['cohort_sha256']:raise ValueError('Supplement belongs to different source freeze')
    original=pd.read_csv(DATA/'frozen/modeling_cohort.csv',keep_default_na=False)
    source={r['id']:r for r in original[original.split.eq('held_out_test')].to_dict('records')}
    decisions={r['id']:r for r in read_json(base/'semantic_decisions.json')}
    seen=set()
    for r in rows:
        ident=r['frame_id'];key=(ident,r['condition'])
        if key in seen or ident not in source:raise ValueError('Duplicate or non-held-out supplemental row')
        seen.add(key)
        if r['label']!=source[ident]['label'] or r['source_text_sha256']!=digest(source[ident]['safe_text']) or r['text_sha256']!=digest(r['text']):raise ValueError('Supplement source/text hash mismatch')
        if r['condition']=='C0':
            if r['text']!=source[ident]['safe_text']:raise ValueError('C0 differs from frozen source')
            continue
        full_id=ident+'::'+r['condition'];d=decisions[full_id]
        if not d['approved'] or d['source']!=source[ident]['safe_text'] or d['text']!=r['text']:raise ValueError('Unapproved supplemental row')
        if invariant_errors(d['source'],d['text'],d['condition'],d['institution_hint']):raise ValueError('Deterministic supplemental invariants failed')
        payload,output=call('G',r['generation_request_sha256'])
        if output[full_id]['text']!=r['text'] or payload[full_id]['source']!=d['source']:raise ValueError('Generation evidence mismatch')
        for role in ['A','B','J']:
            assessment=d.get(role)
            if not assessment:continue
            input_items,output_items=call(role,assessment['review_request_sha256'])
            supplied=input_items[full_id]
            expected={k:v for k,v in assessment.items() if k!='review_request_sha256'}
            if output_items[full_id]!=expected or supplied['text']!=r['text'] or supplied['source']!=d['source']:raise ValueError('Semantic review evidence mismatch')
            if role=='J' and (supplied.get('A')!=d['A'] or supplied.get('B')!=d['B']):raise ValueError('Supplement adjudication chain mismatch')
        accepted=(approved(d.get('A')) and approved(d.get('B'))) or (approved(d.get('A'))!=approved(d.get('B')) and approved(d.get('J')))
        if not accepted:raise ValueError('Supplement approval cannot be reconstructed')
    if sum(r['condition']=='C0' for r in rows)!=35:raise ValueError('Incomplete supplemental source anchors')
    return rows,manifest


def modern_cache(prepared=None):
    from .modernbert import predict_proba,verify_frozen_model
    rows,manifest=prepared if prepared is not None else verify_supplement();directory=MODELS/'modernbert';verify_frozen_model(directory)
    key=file_digest(directory/'best_checkpoint/model.safetensors')
    ids=[r['frame_id']+'::'+r['condition'] for r in rows]
    cache_path=RESULTS/'experiment_C_robustness/modernbert_prediction_cache.json'
    if cache_path.exists():
        cache=read_json(cache_path);validate_probability_cache(cache,ids,key,manifest['frozen_sha256']);return
    p=predict_proba([r['text'] for r in rows],directory/'best_checkpoint')
    cache={'ids':ids,'probabilities':list(map(float,p)),'model_sha256':key,'cohort_sha256':manifest['frozen_sha256']}
    validate_probability_cache(cache,ids,key,manifest['frozen_sha256']);save_json(cache_path,cache)
    print(f'Frozen supplemental ModernBERT rows scored: {len(p)}')


def evaluate(prepared=None):
    rows,manifest=prepared if prepared is not None else verify_supplement();directory=MODELS/'primary/lexical';models=read_json(directory/'model_manifest.json')
    frozen=verify_frozen_inputs('primary')
    if models['frozen_cohort_sha256']!=frozen['cohort_sha256'] or models['protocol_sha256']!=frozen['protocol_sha256']:raise ValueError('Wrong lexical training freeze')
    vectorizer=None;scored={};model_hashes={}
    for name,record in models['models'].items():
        verify_hash(directory/record['file'],record['sha256']);model=joblib.load(directory/record['file'])
        vectorizer=model.named_steps['tfidf'];scored[name]=probabilities(model,[r['text'] for r in rows]);model_hashes[name]=record['sha256']
    modern=MODELS/'modernbert';m=read_json(modern/'model_manifest.json')
    for p,h in m['files'].items():verify_hash(modern/p,h)
    key=file_digest(modern/'best_checkpoint/model.safetensors');cache=read_json(RESULTS/'experiment_C_robustness/modernbert_prediction_cache.json')
    validate_probability_cache(cache,[r['frame_id']+'::'+r['condition'] for r in rows],key,manifest['frozen_sha256'])
    scored['ModernBERT']=np.asarray(cache['probabilities']);model_hashes['ModernBERT']=key
    originals={r['frame_id']:r for r in rows if r['condition']=='C0'}
    records=[]
    for name,prob in scored.items():
        baseline={r['frame_id']:float(v) for r,v in zip(rows,prob) if r['condition']=='C0'}
        for r,value in zip(rows,prob):
            source=originals[r['frame_id']]['text'];x=vectorizer.transform([source,r['text']])
            cosine=float(cosine_similarity(x[0],x[1])[0,0]);a=set(source.casefold().split());b=set(r['text'].casefold().split())
            records.append(r|{'model':name,'model_sha256':model_hashes[name],'probability':float(value),'prediction':int(value>=.5),
                  'original_probability':baseline[r['frame_id']],'signed_delta':baseline[r['frame_id']]-float(value),
                  'absolute_delta':abs(baseline[r['frame_id']]-float(value)),
                  'threshold_transition':f'{int(baseline[r["frame_id"]]>=.5)}->{int(value>=.5)}',
                  'token_jaccard':len(a&b)/len(a|b) if a|b else 1.,'normalized_edit_distance':1-SequenceMatcher(None,source,r['text'],autojunk=False).ratio(),
                  'tfidf_cosine_distance':1-cosine})
    out=RESULTS/'experiment_C_robustness';save_csv(out/'predictions.csv',records)
    df=pd.DataFrame(records);summary=[];effects=[]
    for (name,condition),part in df.groupby(['model','condition'],sort=True):
        result=metrics(part.label.map({'legitimate':0,'phishing':1}),part.probability)
        changed=part[part.condition.ne('C0')]
        summary.append({'model':name,'condition':condition,**result,
              'mean_signed_delta':float(part.signed_delta.mean()),'median_signed_delta':float(part.signed_delta.median()),
              'mean_absolute_delta':float(part.absolute_delta.mean()),'threshold_crossings':int(part.threshold_transition.isin(['0->1','1->0']).sum()),
              'new_false_positives':int((part.label.eq('legitimate')&part.threshold_transition.eq('0->1')).sum()),
              'recovered_false_positives':int((part.label.eq('legitimate')&part.threshold_transition.eq('1->0')).sum()),
              'already_false_positive':int((part.label.eq('legitimate')&(part.original_probability>=.5)).sum()),
              'scope':'available_pairs_exploratory_selective_attrition'})
    for (name,label),part in df[df.condition.ne('C0')].groupby(['model','label']):
        frame_effects=[]
        for fid,g in part.groupby('frame_id'):
            if len(g)<2 or g.tfidf_cosine_distance.std()<1e-12:continue
            slope=float(np.polyfit(g.tfidf_cosine_distance,g.absolute_delta,1)[0]);frame_effects.append(slope)
        rng=np.random.default_rng(42)
        bootstrap=rng.choice(frame_effects,(10000,len(frame_effects)),replace=True).mean(axis=1) if frame_effects else None
        effects.append({'model':name,'label':label,'paired_variants':len(part),'frames_with_slope':len(frame_effects),
              'mean_within_frame_abs_change_slope':float(np.mean(frame_effects)) if frame_effects else None,
              'ci95_low':float(np.quantile(bootstrap,.025)) if bootstrap is not None else None,
              'ci95_high':float(np.quantile(bootstrap,.975)) if bootstrap is not None else None,
              'scope':'descriptive_frame_bootstrap_only_no_causality_no_confirmatory_pvalues'})
    save_csv(out/'condition_metrics.csv',summary);save_csv(out/'distance_association.csv',effects)
    extremes=df[df.condition.ne('C0')].sort_values(['absolute_delta','frame_id','condition'],ascending=[False,True,True])
    save_csv(out/'extreme_cases.csv',extremes.to_dict('records'))
    complete=manifest['complete_core_frames'];trajectory=df[df.frame_id.isin(complete)&df.condition.ne('C0')].groupby('frame_id').absolute_delta.mean()
    representative=min(trajectory.index,key=lambda i:(abs(trajectory[i]-trajectory.median()),i)) if len(trajectory) else None
    save_csv(out/'representative_complete_trajectory.csv',df[df.frame_id.eq(representative)].to_dict('records'))
    status={'status':'EXPLORATORY_AVAILABLE_PAIR_SUPPLEMENT_ONLY','primary_C_status':'NOT RUN minimum control gate unmet',
         'source_frames':manifest['source_frames'],'approved_variants':manifest['accepted_rewrites'],'frozen_rows':len(rows),'complete_core_frames':len(complete),'complete_core_labels':manifest['complete_core_labels'],
         'threshold_crossings_by_model':{name:sum(r['threshold_transition'] in ['0->1','1->0'] for r in records if r['model']==name) for name in scored},
         'representative_complete_frame':representative,'representative_selection':'closest median frame-average absolute movement across all3models, stable ID tie-break; phishing-only complete support',
         'largest_extreme':extremes.iloc[0][['frame_id','condition','model','absolute_delta','signed_delta','threshold_transition']].to_dict(),
         'predictions_sha256':file_digest(out/'predictions.csv'),'frozen_variant_sha256':manifest['frozen_sha256'],
         'model_hashes':model_hashes,'supplement_plan_sha256':file_digest(CONFIG/'robustness_supplement_plan.json'),
         'warnings':['Allapprovedrewritesrequiredadjudication','No corrected held-out legitimate rewrites' if not any(r['label']=='legitimate' and r['condition']!='C0' for r in rows) else 'At most one legitimate rewrite per condition','Selectiveattrition;conditionmeansdifferentcohorts','Noformalconditionrankingorcontextualsuperiorityclaim']}
    save_json(out/'analysis_summary.json',status);print(json.dumps(status,indent=2))


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--modernbert-only',action='store_true');a=p.parse_args();modern_cache() if a.modernbert_only else evaluate()
