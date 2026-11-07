import copy
import hashlib
import json
import pytest


def config():
    return {'roles':{'llm_reviewer_A':'fixture-A','llm_reviewer_B':'fixture-B'},'review_temperature':0.,
            'review_top_p':1.,'review_max_output_tokens':1200}


def store(tmp_path,role='llm_reviewer_A',payload=None,output=None):
    from src.benchmark_v2_1.automated_evidence import expected_request
    from src.benchmark_v2_1.core import digest
    payload=payload or {'frame_id':'F1','safe_text':'safe'};output=output or {'safe':True}
    schema={'type':'object','properties':{'safe':{'type':'boolean'}},'required':['safe'],'additionalProperties':False}
    request=expected_request(config(),role,'review',payload,schema)
    key=digest(json.dumps({'role':role,'request':request},sort_keys=True,ensure_ascii=False))
    record={'request_hash':key,'role':role,'status':'completed','model':config()['roles'][role],
            'response_id':'fixture','output':output,'raw_response':{'id':'fixture','model':config()['roles'][role],
            'output':[{'content':[{'type':'output_text','text':json.dumps(output)}]}]}}
    (tmp_path/f'{key}.request.json').write_text(json.dumps({'request_hash':key,'role':role,'raw_request':request}),encoding='utf-8')
    (tmp_path/f'{key}.result.json').write_text(json.dumps(record),encoding='utf-8')
    return key,schema,payload


def test_review_cache_is_bound_to_role_frame_prompt_and_raw_output(tmp_path):
    from src.benchmark_v2_1.automated_evidence import verify_call
    key,schema,payload=store(tmp_path)
    verify_call(key,'llm_reviewer_A','review',payload,schema,config(),calls=tmp_path)
    with pytest.raises(ValueError):verify_call(key,'llm_reviewer_B','review',payload,schema,config(),calls=tmp_path)
    with pytest.raises(ValueError):verify_call(key,'llm_reviewer_A','review',{**payload,'frame_id':'F2'},schema,config(),calls=tmp_path)
    path=tmp_path/f'{key}.result.json';d=json.loads(path.read_text());d['output']['safe']=False;path.write_text(json.dumps(d))
    with pytest.raises(ValueError):verify_call(key,'llm_reviewer_A','review',payload,schema,config(),calls=tmp_path)


def test_cached_prediction_hash_cannot_be_skipped(tmp_path):
    from src.benchmark_v2_1.automated_evidence import load_prediction_cache
    p=tmp_path/'predictions.csv';p.write_text('x\n1\n')
    m=tmp_path/'manifest.json';models=[{'path':'model','sha256':'fixed'}]
    m.write_text(json.dumps({'predictions_sha256':hashlib.sha256(p.read_bytes()).hexdigest(),
        'frozen_data_sha256':'source','models':models}))
    assert len(load_prediction_cache(p,m,'source',models))==1
    p.write_text('x\n2\n')
    with pytest.raises(ValueError):load_prediction_cache(p,m,'source',models)
