"""Prespecified seven-member Holm family with strict paired frame inputs."""
import json
import numpy as np
import pandas as pd
from .core import DATA, RESULTS, validate_predictions, write_csv, write_json
from .statistics import one_sample, holm, mean_ci

CONTRASTS=[('H5_C0_C1','C0','C1'),('H6_C2_C3','C2','C3'),('H7_C0_C4','C0','C4'),('H8_C0_C5','C0','C5'),('H9_C0_C6','C0','C6')]


def analyze(data):
    validate_predictions(data)
    data=data[data.true_label.eq('phishing_scam')].copy()
    if data.empty:raise ValueError('No phishing frames for primary analysis')
    for key in ['surface_distance','jaccard_similarity','normalized_edit_distance','tfidf_cosine_similarity']:
        values=pd.to_numeric(data[key],errors='raise')
        if not np.isfinite(values).all() or not values.between(0,1).all():raise ValueError('Invalid distances')
    effects={key:[] for key in ['H1_DISTANCE_LOGIT','H2_DISTANCE_FN',*[x[0] for x in CONTRASTS]]}
    for frame_id,g in data.groupby('frame_id'):
        g=g.set_index('condition');x=g.surface_distance.to_numpy(dtype=float)
        if np.ptp(x)<=0:raise ValueError('Undefined within-frame distance slope; report design failure')
        logits=[];misses=[]
        for model in ('lr','rf'):
            p=g[f'{model}_probability'].astype(float).clip(1e-6,1-1e-6)
            logits.append(np.log(p/(1-p)));misses.append(1-g[f'{model}_prediction'].astype(int))
        logit=(logits[0]+logits[1])/2;fn=(misses[0]+misses[1])/2
        effects['H1_DISTANCE_LOGIT'].append(float(np.polyfit(x,logit,1)[0]))
        effects['H2_DISTANCE_FN'].append(float(np.polyfit(x,fn,1)[0]))
        for name,before,after in CONTRASTS:effects[name].append(float(logit[after]-logit[before]))
    rows=[]
    for key,values in effects.items():
        estimate=one_sample(values);ci=mean_ci(values)
        rows.append({'hypothesis_id':key,**estimate,'ci95_low':ci[0],'ci95_high':ci[1]})
    # Missing/undefined tests remain in the family as p=1 for adjustment only.
    adjusted=holm([r['p_value'] if r['p_value'] is not None else 1. for r in rows])
    for row,p in zip(rows,adjusted):
        row['holm_adjusted_p']=p if row['p_value'] is not None else None
        row['reject_holm_0_05']=row['p_value'] is not None and p<=.05
    return rows


def main():
    path=DATA/'evaluation/predictions.csv'
    if not path.exists():
        write_json(RESULTS/'diagnostics/analysis_status.json',{'status':'NOT RUN','reason':'No frozen reviewed detector predictions'})
        print('NOT RUN: no frozen reviewed detector predictions');return
    data=pd.read_csv(path,keep_default_na=False);rows=analyze(data)
    write_csv(DATA/'analysis/confirmatory.csv',rows,list(rows[0]))
    write_json(RESULTS/'diagnostics/analysis_status.json',{'status':'RUN','family':'canonical-frozen-space-v1','tests':7,'correction':'Holm','seed':42})


if __name__=='__main__':main()
