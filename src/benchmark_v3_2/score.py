"""Distances and scoring from read-only frozen model artifacts; no fitting."""
import argparse
import numpy as np
from difflib import SequenceMatcher
from .core import *
from .generate import verify_prefreeze

def align_distances(rows,dist):
    expected={(r['frame_id'],r['condition']):r for r in rows}
    lookup={(r['frame_id'],r['condition']):r for r in dist}
    if len(dist)!=len(rows) or len(lookup)!=len(dist) or set(lookup)!=set(expected):raise ValueError('Analysis matrix frame/condition mismatch')
    if any(lookup[k]['text_sha256']!=r['text_sha256'] or lookup[k]['text']!=r['text'] for k,r in expected.items()):raise ValueError('Analysis text mismatch')
    return lookup

def matrix():
    verify_prefreeze();manifest=read(DATA/'frozen/matrix_manifest.json')
    for path,key in [(DATA/'frozen/robustness_matrix.csv','matrix_sha256'),(DATA/'review/rewrite_decisions.json','decisions_sha256'),(MODELS/'MODEL_FREEZE_MANIFEST.json','model_freeze_sha256'),(DOCS/'STATISTICAL_ANALYSIS_PLAN.md','statistical_plan_sha256')]:
        if file_sha(path)!=manifest[key]:raise ValueError('Matrix/freeze evidence changed')
    return csv_rows(DATA/'frozen/robustness_matrix.csv')

def manipulation():
    import joblib
    from sklearn.metrics.pairwise import cosine_similarity
    rows=matrix();sources={r['frame_id']:r for r in rows if r['condition']=='C0'}
    lr=next(m for m in read(MODELS/'MODEL_FREEZE_MANIFEST.json')['models'] if m['model_name']=='LR')
    vectorizer=joblib.load(ROOT/lr['model_path']).named_steps['tfidf']
    decisions={(d['frame_id'],d['condition'],str(d['attempt'])):d for d in read(DATA/'review/rewrite_decisions.json')}
    def tokens(s):return set(re.findall(r'\w+|\[[^]]+\]',s.casefold()))
    distances=[];analysis=[]
    for r in rows:
        original=sources[r['frame_id']]['text'];a,b=tokens(original),tokens(r['text'])
        jaccard=len(a&b)/len(a|b) if a|b else 1.
        edit=1-SequenceMatcher(None,original,r['text'],autojunk=False).ratio()
        cosine=float(cosine_similarity(vectorizer.transform([original]),vectorizer.transform([r['text']]))[0,0])
        dist={'frame_id':r['frame_id'],'condition':r['condition'],'true_label':r['true_label'],'token_jaccard':jaccard,'normalized_edit_distance':edit,'frozen_tfidf_cosine_similarity':cosine,'surface_distance':.5*(1-jaccard)+.5*edit,'semantic_similarity_if_available':'','semantic_preserved':True,'primary_complete_case':r['primary_complete_case']}
        if r['condition']!='C0':distances.append(dist)
        analysis.append(r|{'surface_distance':dist['surface_distance']})
    write_csv(RESULTS/'manipulation/per_variant_distances.csv',distances)
    write_csv(DATA/'frozen/analysis_matrix.csv',analysis)
    summary=[]
    for c in CONDITIONS[1:]:
        part=[d for d in distances if d['condition']==c]
        summary.append({'condition':c,'N':len(part),**{k:float(np.mean([d[k] for d in part])) if part else '' for k in ['token_jaccard','normalized_edit_distance','frozen_tfidf_cosine_similarity','surface_distance']},'semantic_similarity':'NOT_AVAILABLE','semantic_preservation':'automated approval, not measured embedding similarity'})
    write_csv(RESULTS/'manipulation/condition_summary.csv',summary)
    lookup={(d['frame_id'],d['condition']):d for d in distances}
    pairs=[]
    for ident in sorted(sources):
        if (ident,'C1') in lookup and (ident,'C6') in lookup:
            d1=lookup[ident,'C1']['surface_distance'];d6=lookup[ident,'C6']['surface_distance']
            pairs.append({'frame_id':ident,'C1_surface_distance':d1,'C6_surface_distance':d6,'C6_minus_C1':d6-d1,'C6_greater':d6>d1})
    write_csv(RESULTS/'manipulation/condition_overlap.csv',pairs,['frame_id','C1_surface_distance','C6_surface_distance','C6_minus_C1','C6_greater'])
    failed=[{'frame_id':d['frame_id'],'condition':d['condition'],'attempt':d['attempt'],'deterministic_errors':';'.join(d['deterministic_errors']),'semantic_approved':approved_rewrite(d.get('A')) and approved_rewrite(d.get('B')),'reason':'deterministic_or_semantic_rejected'} for d in read(DATA/'review/rewrite_decisions.json') if not d['approved']]
    write_csv(RESULTS/'manipulation/manipulation_failures.csv',failed,['frame_id','condition','attempt','deterministic_errors','semantic_approved','reason'])
    immutable_json(RESULTS/'manipulation/manifest.json',{'analysis_matrix_sha256':file_sha(DATA/'frozen/analysis_matrix.csv'),'frozen_matrix_sha256':file_sha(DATA/'frozen/robustness_matrix.csv'),'distance_file_sha256':file_sha(RESULTS/'manipulation/per_variant_distances.csv'),'vectorizer_model_sha256':lr['sha256'],'method':'surface=.5*(1-tokenJaccard)+.5*normalizedSequenceMatcherDistance; lexical cosine is not semantic similarity'})
    return rows

def modern():
    from src.benchmark_v3.modernbert import predict_proba
    rows=matrix();freeze=read(MODELS/'MODEL_FREEZE_MANIFEST.json');m=next(m for m in freeze['models'] if m['model_name']=='ModernBERT')
    path=RESULTS/'predictions/modernbert_cache.json'
    if path.exists():
        cache=read(path)
        if cache['matrix_sha256']!=file_sha(DATA/'frozen/robustness_matrix.csv') or cache['model_sha256']!=m['sha256']:raise ValueError('Cache binding')
        return
    values=predict_proba([r['text'] for r in rows],(ROOT/m['model_path']).parent)
    immutable_json(path,{'ids':[r['frame_id']+'::'+r['condition'] for r in rows],'probabilities':values,'matrix_sha256':file_sha(DATA/'frozen/robustness_matrix.csv'),'model_sha256':m['sha256'],'frozen_at':now()})
    print('Frozen ModernBERT scored',len(rows),flush=True)

def evaluate():
    import joblib
    from src.benchmark_v3.baselines import probabilities
    rows=matrix();dist=csv_rows(DATA/'frozen/analysis_matrix.csv');freeze=read(MODELS/'MODEL_FREEZE_MANIFEST.json')
    evidence=read(RESULTS/'manipulation/manifest.json')
    if file_sha(DATA/'frozen/analysis_matrix.csv')!=evidence['analysis_matrix_sha256'] or file_sha(DATA/'frozen/robustness_matrix.csv')!=evidence['frozen_matrix_sha256']:raise ValueError('Manipulation input hash mismatch')
    lookup=align_distances(rows,dist)
    outputs={}
    for m in freeze['models']:
        name=m['model_name']
        if name=='ModernBERT':
            cache=read(RESULTS/'predictions/modernbert_cache.json')
            if cache['ids']!=[r['frame_id']+'::'+r['condition'] for r in rows] or cache['model_sha256']!=m['sha256'] or cache['matrix_sha256']!=file_sha(DATA/'frozen/robustness_matrix.csv'):raise ValueError('Modern cache inputs')
            values=cache['probabilities']
        else:values=list(map(float,probabilities(joblib.load(ROOT/m['model_path']),[r['text'] for r in rows])))
        if len(values)!=len(rows) or any(not np.isfinite(x) or not 0<=x<=1 for x in values):raise ValueError('Bad probabilities')
        anchors={r['frame_id']:p for r,p in zip(rows,values) if r['condition']=='C0'}
        result=[]
        for r,p in zip(rows,values):
            d=lookup[r['frame_id'],r['condition']]
            p0=anchors[r['frame_id']];label=int(r['true_label']);y=int(p>=.5);y0=int(p0>=.5)
            result.append({'frame_id':r['frame_id'],'condition':r['condition'],'true_label':label,'probability':p,'prediction':y,'C0_probability':p0,'signed_delta':p0-p,'absolute_delta':abs(p0-p),'threshold_transition':f'{y0}->{y}','primary_complete_case':r['primary_complete_case'],'surface_distance':d['surface_distance'],'model_sha256':m['sha256'],'text_sha256':r['text_sha256']})
        write_csv(RESULTS/f'predictions/{name}_predictions.csv',result);outputs[name]=len(result)
    manifest_path=RESULTS/'predictions/prediction_manifest.json'
    timestamp=read(manifest_path)['scored_at'] if manifest_path.exists() else now()
    immutable_json(manifest_path,{'matrix_sha256':file_sha(DATA/'frozen/robustness_matrix.csv'),'model_freeze_sha256':file_sha(MODELS/'MODEL_FREEZE_MANIFEST.json'),'files':{n:file_sha(RESULTS/f'predictions/{n}_predictions.csv') for n in outputs},'scored_at':timestamp,'rows_per_model':outputs})
    print('Frozen model scoring',outputs,flush=True)

def replay():
    from src.benchmark_v3.modernbert import predict_proba
    rows=matrix();m=next(m for m in read(MODELS/'MODEL_FREEZE_MANIFEST.json')['models'] if m['model_name']=='ModernBERT')
    cached=read(RESULTS/'predictions/modernbert_cache.json')
    values=predict_proba([r['text'] for r in rows],(ROOT/m['model_path']).parent)
    difference=float(np.max(np.abs(np.array(values)-np.array(cached['probabilities'])))) if values else 0.
    if difference>1e-7:raise ValueError('ModernBERT numerical replay differs')
    immutable_json(RESULTS/'predictions/modernbert_replay.json',{'model_sha256':m['sha256'],'matrix_sha256':file_sha(DATA/'frozen/robustness_matrix.csv'),'N':len(rows),'max_absolute_difference':difference,'new_fit_performed':False})
    print('ModernBERT independent replay max difference',difference,flush=True)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('stage',choices=['manipulation','modern','evaluate','replay']);a=p.parse_args();globals()[a.stage]()
