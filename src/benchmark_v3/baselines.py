"""Fair v3 LR/RF: same training texts and exactly the same fitted TF-IDF."""
import argparse
import json
from pathlib import Path
import joblib
import numpy as np
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier
from sklearn.pipeline import Pipeline
from .core import DATA, MODELS, CONFIG, digest, save_json, read_json, verify_hash


def fit_models(texts, labels):
    if set(labels)!={0,1}: raise ValueError('Both legitimate and phishing TRAIN labels required')
    vectorizer=TfidfVectorizer(ngram_range=(1,2),max_features=20000,min_df=1)
    x=vectorizer.fit_transform(texts)
    classifiers={'LR':LogisticRegression(C=1.,max_iter=2000,random_state=42),
                 'RF':RandomForestClassifier(n_estimators=200,random_state=42,n_jobs=4)}
    return {name:Pipeline([('tfidf',vectorizer),('classifier',classifier.fit(x,labels))]) for name,classifier in classifiers.items()}


def probabilities(model,texts):
    classes=list(model.classes_)
    if classes!=[0,1]: raise ValueError('Unexpected classifier class mapping')
    values=np.asarray(model.predict_proba(texts)[:,classes.index(1)],dtype=float)
    if not np.all(np.isfinite(values)) or np.any((values<0)|(values>1)): raise ValueError('Invalid classifier probability')
    return values


def train(experiment='primary'):
    from .protocol import verify_frozen_inputs
    freeze=verify_frozen_inputs(experiment)
    name='modeling_cohort.csv' if experiment=='primary' else 'source_holdout_cohort.csv'
    expected=freeze['cohort_sha256' if experiment=='primary' else 'source_holdout_cohort_sha256']
    path=DATA/'frozen'/name;verify_hash(path,expected)
    rows=pd.read_csv(path,keep_default_na=False)
    training=rows[rows.split.eq('train')]
    labels=training.label.map({'legitimate':0,'phishing':1}).tolist()
    output=MODELS/experiment/'lexical';output.mkdir(parents=True,exist_ok=True)
    manifest_path=output/'model_manifest.json'
    if manifest_path.exists():
        record=read_json(manifest_path)
        if record['frozen_cohort_sha256']!=expected or record['protocol_sha256']!=freeze['protocol_sha256']: raise ValueError('Cached models trained on different cohort/protocol')
        for model in record['models'].values(): verify_hash(output/model['file'],model['sha256'])
        return record
    models=fit_models(training.safe_text.tolist(),labels)
    records={}
    for model_name,model in models.items():
        target=output/f'{model_name}.joblib'
        with target.open('xb') as handle:joblib.dump(model,handle)
        records[model_name]={'file':target.name,'sha256':digest(target.read_bytes()),'class_mapping':{'0':'legitimate','1':'phishing'}}
    record={'status':'FROZEN_EXPLORATORY','experiment':experiment,'frozen_cohort_sha256':expected,
       'training_rows':len(training),'training_labels':training.label.value_counts().to_dict(),'models':records,
       'fitted_feature_count':len(models['LR'].named_steps['tfidf'].vocabulary_),
       'identical_fitted_tfidf':models['LR'].named_steps['tfidf'] is models['RF'].named_steps['tfidf'],
       'protocol_sha256':digest((CONFIG/'experiment_protocol.json').read_bytes()),'threshold':.5,
       'test_used_for_fitting_or_tuning':False,'hyperparameters':'fixed prospectively in experiment_protocol.json'}
    save_json(manifest_path,record)
    print(json.dumps(record,indent=2))
    return record


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--experiment',choices=['primary','source_holdout'],default='primary');a=p.parse_args();train(a.experiment)
