"""Extract actual file counts and fitted model metadata without predicting or fitting."""
import hashlib
import json
import joblib
import pandas as pd
from .core import ROOT, RESULTS, write_json
from .freeze_benchmark import model_records


def main():
    result={'status':'READ_ONLY_MODEL_INSPECTION','models':[],'csv_inventory':[]}
    for record in model_records():
        pipeline=joblib.load(ROOT/record['path']);v=pipeline.named_steps['tfidf'];cl=pipeline.named_steps['classifier']
        vocab=json.dumps(v.vocabulary_,sort_keys=True,default=int)
        result['models'].append({**record,'classes':pipeline.classes_.tolist(),'threshold':.5,
            'vectorizer_parameters':{k:str(value) for k,value in v.get_params().items()},
            'classifier_parameters':{k:str(value) for k,value in cl.get_params().items()},
            'vocabulary_size':len(v.vocabulary_),'vocabulary_sha256':hashlib.sha256(vocab.encode()).hexdigest(),
            'idf_sha256':hashlib.sha256(v.idf_.tobytes()).hexdigest(),
            'training_input':'data/final/sms_master_with_splits.csv','training_split':'train',
            'training_rows_metadata':1568,'training_data_file_sha256':hashlib.sha256((ROOT/'data/final/sms_master_with_splits.csv').read_bytes()).hexdigest()})
    for path in sorted((ROOT/'data').rglob('*.csv')):
        try:
            f=pd.read_csv(path,low_memory=False);result['csv_inventory'].append({'path':path.relative_to(ROOT).as_posix(),'rows':len(f),'columns':list(f.columns)})
        except Exception as e:result['csv_inventory'].append({'path':path.relative_to(ROOT).as_posix(),'error':type(e).__name__})
    baseline=pd.read_csv(ROOT/'docs/benchmark_v2_1/BASELINE_INVENTORY.csv',encoding='utf-8-sig')
    result['changed_baseline_files']=[r.path for r in baseline.itertuples() if not (ROOT/r.path).exists() or hashlib.sha256((ROOT/r.path).read_bytes()).hexdigest()!=r.sha256]
    write_json(RESULTS/'diagnostics/runtime_audit.json',result)
    print(f"{len(result['csv_inventory'])} CSV files inspected; baseline changes: {result['changed_baseline_files']}")


if __name__=='__main__':main()
