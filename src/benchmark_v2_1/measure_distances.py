"""Measure completed text before detector scoring, using frozen vectorizers only."""
import argparse
import hashlib
from pathlib import Path
import joblib
import numpy as np
import pandas as pd
from analysis.benchmark_v2_1_distance_metrics import jaccard, normalized_edit_distance
from .core import ROOT, DATA, RESULTS, VARIANT_FIELDS, write_csv, write_json
from .freeze_benchmark import model_records


def measure(data,vectorizers):
    data=data.copy();a=data.defanged_text.tolist();b=data.variant_text.tolist()
    data['jaccard_similarity']=[jaccard(x,y) for x,y in zip(a,b)]
    data['normalized_edit_distance']=[normalized_edit_distance(x,y) for x,y in zip(a,b)]
    identical=np.array([x==y for x,y in zip(a,b)])
    for model,v in vectorizers.items():
        x=v.transform(a);y=v.transform(b)
        # Fitted TF-IDF vectors are L2 normalized. Define identity similarity as 1,
        # including identical out-of-vocabulary texts; other zero overlaps are 0.
        data[f'{model}_tfidf_cosine_similarity']=np.where(identical,1.,np.clip(np.asarray(x.multiply(y).sum(axis=1)).ravel(),0,1))
    data['tfidf_cosine_similarity']=(data.lr_tfidf_cosine_similarity+data.rf_tfidf_cosine_similarity)/2
    data['surface_distance']=((1-data.jaccard_similarity)+data.normalized_edit_distance+(1-data.tfidf_cosine_similarity))/3
    return data


def main():
    p=argparse.ArgumentParser();p.add_argument('--input',type=Path,default=DATA/'generated/variant_matrix.csv');a=p.parse_args()
    frame=pd.read_csv(a.input,keep_default_na=False);frame=frame[frame.variant_text.ne('')]
    vectors={}
    for record in model_records():
        name='lr' if 'logistic' in record['path'] else 'rf'
        vectors[name]=joblib.load(ROOT/record['path']).named_steps['tfidf']
    measured=measure(frame,vectors)
    write_csv(DATA/'generated/distance_measurements.csv',measured.to_dict('records'),VARIANT_FIELDS)
    wide=measured.pivot(index='frame_id',columns='condition',values='surface_distance')
    complete=set(f'C{i}' for i in range(7)).issubset(wide.columns) and not wide.isna().any().any()
    state={'status':'PENDING_GENERATION_AND_HUMAN_VALIDATION','measured_texts':len(frame),'complete_frames':len(wide) if complete else 0,
           'input_sha256':hashlib.sha256(a.input.read_bytes()).hexdigest(),
           'models':model_records(),
           'representation':'frozen-vectorizer-equal-weight-v1','C1_lower_than_C5':None,'C1_lower_than_C6':None}
    if complete:
        state.update(C1_lower_than_C5=bool((wide.C1<wide.C5).mean()>=.8),C1_lower_than_C6=bool((wide.C1<wide.C6).mean()>=.8),
                     C1_C5_pair_fraction=float((wide.C1<wide.C5).mean()),C1_C6_pair_fraction=float((wide.C1<wide.C6).mean()),
                     status='OBJECTIVE_MEASUREMENTS_COMPLETE_HUMAN_VALIDATION_PENDING')
    write_json(RESULTS/'diagnostics/manipulation_check.json',state)
    print(f'{len(frame)} completed texts measured; complete seven-condition frames: {state["complete_frames"]}')


if __name__=='__main__':main()
