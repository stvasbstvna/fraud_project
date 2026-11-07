"""Metrics with explicit undefined single-class endpoints; frozen models only."""
import argparse
from collections import Counter
import json
import numpy as np
import pandas as pd
import joblib
from sklearn.metrics import confusion_matrix, roc_auc_score, precision_recall_curve, auc, average_precision_score
from .core import ROOT, DATA, MODELS, RESULTS, digest, save_csv, save_json, read_json, verify_hash, file_digest
from .baselines import probabilities


def metrics(labels, probs):
    y=np.asarray(labels,dtype=int);p=np.asarray(probs,dtype=float)
    if len(y)!=len(p) or not np.all(np.isfinite(p)) or np.any((p<0)|(p>1)):raise ValueError('Invalid paired probabilities')
    pred=(p>=.5).astype(int)
    tn,fp,fn,tp=map(int,confusion_matrix(y,pred,labels=[0,1]).ravel())
    positive=tp+fn; negative=tn+fp
    precision=tp/(tp+fp) if tp+fp else 0.
    recall=tp/positive if positive else None
    f1=2*tp/(2*tp+fp+fn) if 2*tp+fp+fn else 0.
    both=bool(positive and negative)
    curve=precision_recall_curve(y,p) if both else None
    return {'N':len(y),'phishing':positive,'legitimate':negative,'accuracy':float((pred==y).mean()) if len(y) else None,
        'precision':precision,'recall':recall,'F1':f1,'specificity':tn/negative if negative else None,
        'false_negative_rate':fn/positive if positive else None,'false_positive_rate':fp/negative if negative else None,
        'ROC_AUC':float(roc_auc_score(y,p)) if both else None,
        'PR_AUC':float(auc(curve[1],curve[0])) if both else None,
        'average_precision':float(average_precision_score(y,p)) if both else None,
        'TN':tn,'FP':fp,'FN':fn,'TP':tp,'threshold':.5}


def validate_probability_cache(cache, ids, model_sha, cohort_sha):
    if cache['ids']!=ids or cache['model_sha256']!=model_sha or cache['cohort_sha256']!=cohort_sha:
        raise ValueError('Cached ModernBERT evaluation binding mismatch')
    prob=np.asarray(cache['probabilities'])
    if len(prob)!=len(ids) or not np.all(np.isfinite(prob)) or np.any((prob<0)|(prob>1)):
        raise ValueError('Invalid cached ModernBERT probabilities')


def modern_cache(experiment='primary'):
    from .modernbert import predict_proba
    from .protocol import verify_frozen_inputs
    freeze=verify_frozen_inputs(experiment)
    cohort=DATA/'frozen'/('modeling_cohort.csv' if experiment=='primary' else 'source_holdout_cohort.csv')
    expected=freeze['cohort_sha256' if experiment=='primary' else 'source_holdout_cohort_sha256'];verify_hash(cohort,expected)
    frame=pd.read_csv(cohort,keep_default_na=False);test=frame[frame.split.eq('held_out_test' if experiment=='primary' else 'source_test')]
    directory=MODELS/('modernbert' if experiment=='primary' else 'modernbert_source_holdout')
    model_manifest=read_json(directory/'model_manifest.json')
    for name,key in model_manifest['files'].items():verify_hash(directory/name,key)
    if read_json(directory/'training_config.json')['frozen_csv_sha256']!=expected:raise ValueError('ModernBERT trained on different freeze')
    model_sha=file_digest(directory/'best_checkpoint/model.safetensors')
    output=RESULTS/('experiment_A_detection' if experiment=='primary' else 'experiment_B_generalization')/'modernbert_prediction_cache.json'
    if output.exists():
        cache=read_json(output);validate_probability_cache(cache,test.id.tolist(),model_sha,expected);return cache
    values=predict_proba(test.safe_text.tolist(),directory/'best_checkpoint')
    cache={'ids':test.id.tolist(),'probabilities':list(map(float,values)),'model_sha256':model_sha,'cohort_sha256':expected,
           'purpose':'Frozen held-out inference only, dedicated ModernBERT environment; no optimization'}
    validate_probability_cache(cache,test.id.tolist(),model_sha,expected);save_json(output,cache)
    print(f'ModernBERT {experiment}: {len(values)} frozen held-out probabilities cached')
    return cache


def evaluate(experiment='primary', modernbert=False):
    from .protocol import verify_frozen_inputs
    freeze=verify_frozen_inputs(experiment)
    cohort=DATA/'frozen'/('modeling_cohort.csv' if experiment=='primary' else 'source_holdout_cohort.csv')
    expected=freeze['cohort_sha256' if experiment=='primary' else 'source_holdout_cohort_sha256'];verify_hash(cohort,expected)
    frame=pd.read_csv(cohort,keep_default_na=False)
    test=frame[frame.split.eq('held_out_test' if experiment=='primary' else 'source_test')].copy()
    output=RESULTS/('experiment_A_detection' if experiment=='primary' else 'experiment_B_generalization')
    lexical=MODELS/experiment/'lexical';manifest=read_json(lexical/'model_manifest.json')
    if manifest['frozen_cohort_sha256']!=expected or manifest['protocol_sha256']!=freeze['protocol_sha256']: raise ValueError('Wrong training freeze/protocol')
    results=[];predictions=[];by_source=[]
    candidates=[]
    for name,record in manifest['models'].items():
        verify_hash(lexical/record['file'],record['sha256'])
        model=joblib.load(lexical/record['file'])
        candidates.append((name,probabilities(model,test.safe_text.tolist()),record['sha256']))
    if modernbert:
        directory=MODELS/('modernbert' if experiment=='primary' else 'modernbert_source_holdout')
        model_manifest=read_json(directory/'model_manifest.json')
        for path,key in model_manifest['files'].items(): verify_hash(directory/path,key)
        config=read_json(directory/'training_config.json')
        if config['frozen_csv_sha256']!=expected:raise ValueError('ModernBERT training cohort hash mismatch')
        key=file_digest(directory/'best_checkpoint/model.safetensors')
        cache=read_json(output/'modernbert_prediction_cache.json')
        validate_probability_cache(cache,test.id.tolist(),key,expected)
        candidates.append(('ModernBERT',np.asarray(cache['probabilities']),key))
    for name,prob,key in candidates:
        result=metrics(test.label.map({'legitimate':0,'phishing':1}),prob)
        results.append({'model':name,'experiment':experiment,'model_sha256':key,**result})
        for row,value in zip(test.to_dict('records'),prob):
            predictions.append({k:row[k] for k in ['id','template_family_id','source_id','origin_type','label','message_function','safe_text']} |
                {'model':name,'probability':float(value),'prediction':int(value>=.5),'true_binary':int(row['label']=='phishing'),'model_sha256':key})
        for field in ['source_id','origin_type','message_function']:
            for group in sorted(test[field].unique()):
                mask=test[field].eq(group).to_numpy()
                by_source.append({'model':name,'stratum':field,'group':group,**metrics(test.loc[mask,'label'].map({'legitimate':0,'phishing':1}),np.asarray(prob)[mask])})
    suffix='all_models' if modernbert else 'lexical_only'
    save_csv(output/f'predictions_{suffix}.csv',predictions)
    save_csv(output/f'metrics_{suffix}.csv',results)
    save_csv(output/f'stratified_metrics_{suffix}.csv',by_source)
    save_json(output/f'evaluation_manifest_{suffix}.json',{'status':'EXPLORATORY','frozen_cohort_sha256':expected,
        'test_rows':len(test),'test_labels':test.label.value_counts().to_dict(),'predictions_sha256':digest((output/f'predictions_{suffix}.csv').read_bytes()),
        'metrics':results,'control_warning':f'Observed legitimate test count={int(test.label.eq("legitimate").sum())}; no population FPR claim; single-class endpoints undefined when absent',
        'test_used_for_tuning':False})
    print(json.dumps(results,indent=2))


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--experiment',choices=['primary','source_holdout'],default='primary');p.add_argument('--modernbert',action='store_true');p.add_argument('--modernbert-only',action='store_true');a=p.parse_args()
    modern_cache(a.experiment) if a.modernbert_only else evaluate(a.experiment,a.modernbert)
