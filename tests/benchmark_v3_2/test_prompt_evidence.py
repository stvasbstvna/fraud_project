import json
import pytest
from src.benchmark_v3_2 import calls
from src.benchmark_v3_2.core import sha,canonical,immutable_json,write_csv

@pytest.fixture
def recorded(tmp_path,monkeypatch):
    config=tmp_path/'config';config.mkdir()
    prompt=tmp_path/'prompt.txt';prompt.write_bytes(b'Exact frozen prompt\n')
    monkeypatch.setattr(calls,'ROOT',tmp_path);monkeypatch.setattr(calls,'CONFIG',config)
    write_csv(config/'PROMPT_REGISTRY.csv',[dict(prompt_id='generation_C1_v1',phase='C',purpose='generation',condition='C1',version='v1',file_path='prompt.txt',sha256=sha(prompt.read_bytes()),model_role='G')])
    payload={'model':calls.ROLES['G'],'instructions':prompt.read_text(),'input':json.dumps({'items':[{'id':'f::C1::0'}]}),'text':{'format':{'schema':calls.GEN_SCHEMA}}}
    h=sha(canonical(payload));base=tmp_path/'call'
    immutable_json(base.with_suffix('.request.json'),dict(role='G',prompt_id='generation_C1_v1',request_sha256=h,request_payload=payload))
    raw={'model':calls.ROLES['G'],'status':'completed','output':[{'content':[{'type':'output_text','text':json.dumps({'items':[{'id':'f::C1::0','text':'Research fixture rewrite'}]})}]}]}
    immutable_json(base.with_suffix('.response.json'),dict(request_sha256=h,response_sha256=sha(canonical(raw)),raw_response=raw))
    return base,prompt

def test_raw_output_and_exact_prompt_are_bound(recorded):
    base,prompt=recorded
    assert calls.verify_record(base.with_suffix('.response.json'))[0][0]['id']=='f::C1::0'
    prompt.write_text('Changed prompt',encoding='utf-8')
    with pytest.raises(ValueError,match='Prompt/request'):calls.verify_record(base.with_suffix('.response.json'))

def test_raw_response_tampering_is_detected(recorded):
    base,_=recorded;p=base.with_suffix('.response.json')
    value=json.loads(p.read_text());value['raw_response']['output'][0]['content'][0]['text']='{}';p.write_text(json.dumps(value))
    with pytest.raises(ValueError,match='Raw response'):calls.verify_record(p)

def test_registry_missing_or_ambiguous_prompt_is_rejected(recorded):
    assert calls.prompt_record('generation','G','C1')['version']=='v1'
    with pytest.raises(ValueError,match='Ambiguous prompt'):calls.prompt_record('generation','G','C6')
