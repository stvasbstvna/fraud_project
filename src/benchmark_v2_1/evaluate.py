"""Evaluate a hash-verified, human-reviewed freeze with existing pipelines; never fit."""
import hashlib
import json
import joblib
import numpy as np
import pandas as pd
from .core import ROOT, DATA, VARIANT_FIELDS, validate_matrix, validate_predictions, write_csv, write_json
from .freeze_benchmark import model_records
from .measure_distances import measure


def main():
    path=DATA/'frozen/benchmark_v2_1.csv'
    manifest=json.loads((DATA/'frozen/manifest.json').read_text(encoding='utf-8'))
    if manifest['status']!='FROZEN':raise SystemExit('NOT RUN: benchmark is PENDING human/source review and generation')
    if hashlib.sha256(path.read_bytes()).hexdigest()!=manifest['dataset_sha256']:raise ValueError('Frozen dataset changed')
    for rel,expected in manifest['config_hashes'].items():
        if hashlib.sha256((ROOT/rel).read_bytes()).hexdigest()!=expected:raise ValueError('Frozen config changed')
    if model_records()!=manifest['models']:raise ValueError('Model manifest changed')
    data=pd.read_csv(path,keep_default_na=False)
    validate_matrix(data.to_dict('records'))
    if not data.human_review_status.eq('approved').all():raise ValueError('Human approval missing')
    b=data.variant_text.tolist();vectors={};pipelines={}
    for short in ('lr','rf'):
        record=next(r for r in manifest['models'] if ('logistic' if short=='lr' else 'random_forest') in r['path'])
        pipelines[short]=joblib.load(ROOT/record['path']);vectors[short]=pipelines[short].named_steps['tfidf']
    data=measure(data,vectors)
    for short,record in zip(('lr','rf'),manifest['models']):
        # Match the name explicitly rather than trusting manifest order.
        record=next(r for r in manifest['models'] if ('logistic' if short=='lr' else 'random_forest') in r['path'])
        pipeline=pipelines[short]
        classes=list(pipeline.classes_)
        if 1 not in classes:raise ValueError('Phishing class 1 unavailable')
        data[f'{short}_probability']=pipeline.predict_proba(b)[:,classes.index(1)]
        data[f'{short}_prediction']=pipeline.predict(b)
    validate_predictions(data)
    write_csv(DATA/'evaluation/predictions.csv',data.to_dict('records'),VARIANT_FIELDS)
    write_json(DATA/'evaluation/manifest.json',{'status':'EVALUATED','input_sha256':manifest['dataset_sha256'],
        'models':manifest['models'],'rows':len(data),'fit_calls':0,'threshold':.5,
        'distance_version':'frozen-vectorizer-equal-weight-v1'})
    print(f'{len(data)} evaluated rows; no fitting')


if __name__=='__main__':main()
