import hashlib
import json
import sys
import pandas as pd
from tests.benchmark_v2_1.test_pipeline import frame, matrix, reviews


def test_successful_nonpending_freeze_requires_bound_external_evidence(tmp_path,monkeypatch):
    import src.benchmark_v2_1.core as core
    import src.benchmark_v2_1.freeze_benchmark as freeze
    from src.benchmark_v2_1.generate_variants import make_requests
    data=tmp_path/'data';result=tmp_path/'results'
    for name in ['source','generated','review','frozen']:(data/name).mkdir(parents=True)
    (result/'diagnostics').mkdir(parents=True)
    source=frame();sources=pd.DataFrame([source]);sources.to_csv(data/'source/frames.csv',index=False)
    source_reviews=[{'frame_id':'F1','source_sha256':core.source_digest(source),'reviewer':who,'decision':'approved',
                     **{k:'yes' for k in core.REVIEW_FIELDS}} for who in ['A','B']]
    pd.DataFrame(source_reviews).to_csv(data/'review/source_review_completed.csv',index=False)
    requests={r['variant_id']:r for r in make_requests(sources,source_reviews)}
    rows=matrix();envelopes=[]
    for r in rows:
        if r['condition']=='C0':continue
        req=requests[r['variant_id']]
        r.update(generator_provider=req['provider'],generator_model=req['model'],prompt_version=req['prompt_version'],
                 prompt_sha256=req['prompt_sha256'],request_sha256=req['request_sha256'],response_id='fixture-'+r['condition'],
                 generated_at_utc='2026-11-06T00:00:00+00:00')
        envelopes.append({'provider':req['provider'],'model':req['model'],'request_sha256':req['request_sha256'],
            'attempt':1,'response_id':r['response_id'],'timestamp_utc':r['generated_at_utc'],
            'output':{'frame_id':'F1','condition':r['condition'],'text':r['variant_text']}})
    raw=data/'generated/raw.jsonl';raw.write_text('\n'.join(json.dumps(r) for r in envelopes),encoding='utf-8')
    path=data/'generated/variant_matrix.csv';pd.DataFrame(rows).to_csv(path,index=False)
    review=data/'review/review_queue.csv';pd.DataFrame(reviews(rows)).to_csv(review,index=False)
    (result/'diagnostics/manipulation_check.json').write_text(json.dumps({'input_sha256':hashlib.sha256(path.read_bytes()).hexdigest(),
        'models':freeze.model_records(),'C1_lower_than_C5':True,'C1_lower_than_C6':True}),encoding='utf-8')
    (data/'review/pilot_validation.json').write_text(json.dumps({'semantic_action_valid':True,'directness_valid':True,
        'agreement_adjudicated':True,'attrition_rule_frozen':True,'review_file_sha256':hashlib.sha256(review.read_bytes()).hexdigest()}),encoding='utf-8')
    monkeypatch.setattr(core,'DATA',data);monkeypatch.setattr(freeze,'DATA',data);monkeypatch.setattr(freeze,'RESULTS',result)
    monkeypatch.setattr(sys,'argv',['freeze','--responses',str(raw)])
    freeze.main()
    manifest=json.loads((data/'frozen/manifest.json').read_text())
    assert manifest['status']=='FROZEN' and manifest['rows']==7
    assert len(pd.read_csv(data/'frozen/benchmark_v2_1.csv'))==7
