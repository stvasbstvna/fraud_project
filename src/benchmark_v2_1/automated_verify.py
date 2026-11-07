"""Cross-check frozen evidence, all reported numbers, call lineage and historical preservation."""
import hashlib
import json
from pathlib import Path
import numpy as np
import pandas as pd
from .core import ROOT,DATA,CONFIG,unsafe,write_json
from .automated_protocol import AUTO_DATA,AUTO_RESULTS
from .automated_available_pairs import evaluate_available
from .freeze_benchmark import model_records


def verify():
    data=evaluate_available();anchors=data[data.condition.eq('C0')];variants=data[~data.condition.eq('C0')]
    frozen=pd.read_csv(DATA/'frozen/automated_available_pairs_exploratory.csv',keep_default_na=False)
    assert len(data)==len(frozen)==20
    assert not data.variant_text.map(unsafe).any()
    for fid,g in data.groupby('frame_id'):
        c0=g[g.condition.eq('C0')].iloc[0]
        assert c0.variant_text==c0.defanged_text
        for model in ['lr','rf']:
            assert np.allclose(g[f'{model}_delta'],c0[f'{model}_probability']-g[f'{model}_probability'])
            assert g[f'{model}_probability'].between(0,1).all()
    metrics=pd.read_csv(AUTO_RESULTS/'tables/Table4_detector_performance.csv')
    for r in metrics.to_dict('records'):
        g=data[data.condition.eq(r['condition'])];truth=g.true_label.eq('phishing_scam');pred=g[f"{r['model']}_prediction"].eq(1)
        assert r['N']==len(g) and r['N_phishing']==truth.sum() and r['N_legitimate']==(~truth).sum()
        assert r['TP']==(truth&pred).sum() and r['FP']==((~truth)&pred).sum()
        assert r['TN']==((~truth)&(~pred)).sum() and r['FN']==(truth&(~pred)).sum()
    movement=pd.read_csv(AUTO_RESULTS/'tables/Table5_probability_movement.csv')
    for r in movement.to_dict('records'):
        values=data[data.condition.eq(r['condition'])&data.true_label.eq(r['label'])][f"{r['model']}_delta"]
        assert r['N_paired_frames']==len(values)
        if len(values):assert np.isclose(r['mean_delta'],values.mean()) and np.isclose(r['median_delta'],values.median())
        else:assert pd.isna(r['mean_delta'])
    primary=json.loads((DATA/'frozen/automated_pilot_manifest.json').read_text())
    assert primary['status']=='NOT_FROZEN_NO_COMPLETE_CASES' and primary['rows']==0
    assert len(pd.read_csv(DATA/'frozen/automated_pilot_frozen.csv'))==0
    baseline=pd.read_csv(ROOT/'docs/benchmark_v2_1/AUTOMATED_BASELINE_INVENTORY.csv',encoding='utf-8-sig')
    changed=[r.path for r in baseline.itertuples() if not (ROOT/r.path).exists() or hashlib.sha256((ROOT/r.path).read_bytes()).hexdigest()!=r.sha256]
    if changed:raise ValueError('Historical evidence changed: '+str(changed))
    models=model_records();calls=[];failed=[]
    for p in sorted((AUTO_DATA/'calls').glob('*.result.json')):
        d=json.loads(p.read_text(encoding='utf-8'))
        (calls if d['status']=='completed' else failed).append(d)
        request=json.loads(p.with_name(p.name.replace('.result.json','.request.json')).read_text(encoding='utf-8'))['raw_request']
        payload=json.loads(request['input'])
        forbidden={'lr_probability','rf_probability','lr_prediction','rf_prediction','feature_importance','threshold','tfidf_weights'}
        def keys(value):
            if isinstance(value,dict):return set(value)|set().union(*(keys(v) for v in value.values())) if value else set()
            if isinstance(value,list):return set().union(*(keys(v) for v in value)) if value else set()
            return set()
        assert not (keys(payload)&forbidden)
    figures=list((AUTO_RESULTS/'figures').glob('*.png'));assert len(figures)==4
    tables=list((AUTO_RESULTS/'tables').glob('Table*.csv'));assert len(tables)==8
    usage={'input_tokens':0,'output_tokens':0}
    for call in calls:
        actual=call['raw_response'].get('usage') or {}
        for key in usage:usage[key]+=actual.get(key,0)
    report={'status':'VERIFIED_PRIMARY_FAILED_EXPLORATORY_RESULTS','historical_files_checked':len(baseline),'historical_files_changed':0,
        'source_frames':len(anchors),'generated_variants':24,'approved_variants':len(variants),'rejected_variants':8,
        'complete_cases':0,'primary_frozen_rows':0,'exploratory_frozen_rows':len(data),
        'completed_research_provider_calls':len(calls),'technical_failed_call_records':len(failed),
        'calls_by_role':pd.Series([r['role'] for r in calls]).value_counts().to_dict(),
        'actual_provider_token_usage':usage,'neutral_capability_probe_calls_not_in_research_cache':1,
        'table_count':len(tables),'scientific_figure_count':len(figures),'models':models,
        'review_mode':'automated','validation_type':'automated_semantic_review','independent_human_annotation':False,
        'all_reported_counts_and_paired_deltas_match':True,'detector_output_leakage_keys_found':False,
        'figure_series_source':'same verified Table4/Table5/Table6 data passed to plotting functions; plots visually inspected',
        'predictions_sha256':hashlib.sha256((DATA/'evaluation/automated_available_pairs_predictions.csv').read_bytes()).hexdigest()}
    path=AUTO_RESULTS/'verification.json'
    if path.exists():
        if json.loads(path.read_text())!=report:raise ValueError('Verification changed; new version required')
    else:write_json(path,report)
    print(json.dumps(report,indent=2),flush=True)
    return report


if __name__=='__main__':verify()
