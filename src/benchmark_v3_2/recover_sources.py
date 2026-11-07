"""At most one documented technical source-review recovery; no generation retries here."""
from concurrent.futures import ThreadPoolExecutor
from .core import *
from .calls import Client,batches,verify_record
import os

def recover():
    if (DATA/'generated/initial_jobs.json').exists():raise ValueError('Recovery must precede generation')
    failures=[]
    base=DATA/'review/source_review/calls'
    for p in sorted(base.glob('*.error.json')):
        error=read(p)
        if error['error_type'] not in {'APIConnectionError','APITimeoutError'}:continue
        req=read(p.with_name(p.name.replace('.error.json','.request.json')))
        if p.with_name(p.name.replace('.error.json','.response.json')).exists():continue
        failures.append(req)
    plan={'created_at':now(),'source_requests':len(failures),'max_technical_recovery_per_source_request':1,'generation_policy_unchanged':True,'eligible_errors':['APIConnectionError','APITimeoutError'],'unchanged_prompt_and_payload':True,'reason':'Recover missing technical source assessments only, without selecting semantic decisions or observing detector outputs; original failed requests/errors remain preserved'}
    planpath=CONFIG/'source_technical_recovery_v1.json'
    if not planpath.exists():immutable_json(planpath,plan)
    from dotenv import dotenv_values
    from openai import OpenAI
    client=OpenAI(api_key=os.environ.get('OPENAI_API_KEY') or dotenv_values(ROOT/'.env').get('OPENAI_API_KEY'),max_retries=0,timeout=240)
    recovery=DATA/'review/source_review/recovery_calls'
    def one(req):
        stem=recovery/f"{req['role']}_{req['request_sha256']}"
        path=stem.with_suffix('.request.json')
        if path.exists():return
        immutable_json(path,req|{'call_id':req['call_id']+':technical_recovery1','technical_attempt':1,'timestamp':now()})
        try:
            raw=client.responses.create(**req['request_payload']).model_dump(mode='json')
            immutable_json(stem.with_suffix('.response.json'),{'request_sha256':req['request_sha256'],'response_sha256':sha(canonical(raw)),'raw_response':raw,'timestamp':now()})
            verify_record(stem.with_suffix('.response.json'))
        except Exception as e:immutable_json(stem.with_suffix('.error.json'),{'request_sha256':req['request_sha256'],'error_type':type(e).__name__,'reason':str(e),'timestamp':now()})
    with ThreadPoolExecutor(max_workers=4) as pool:list(pool.map(one,failures))
    print('Technical source recoveries attempted',len(failures),flush=True)

def reassemble():
    packets=read(DATA/'source/outbound_packet.json')+read(DATA/'source/additional_outbound_packet.json')
    assessments={'A':{},'B':{},'J':{}}
    for folder in ['calls','recovery_calls']:
        for p in sorted((DATA/f'review/source_review/{folder}').glob('*.response.json')):
            if p.with_name(p.name.replace('.response.json','.error.json')).exists():continue
            items,req=verify_record(p)
            for item in items:assessments[req['role']][item['id']]=item|{'evidence_request_sha256':req['request_sha256'],'review_model':req['request_payload']['model'],'review_prompt_version':req['prompt_id'],'review_timestamp':req['timestamp']}
    client=Client();disputes=[]
    for r in packets:
        ident=r['id'];a=assessments['A'].get(ident);b=assessments['B'].get(ident)
        if a and b and not source_consensus(a,b) and (approved_source(a) or approved_source(b)) and ident not in assessments['J']:disputes.append(r|{'review_A':a,'review_B':b})
    for r in batches(client,'source_review','J',disputes):assessments['J'][r['id']]=r
    decisions=[]
    for r in packets:
        ident=r['id'];a=assessments['A'].get(ident);b=assessments['B'].get(ident);j=assessments['J'].get(ident)
        consensus=bool(a and b and source_consensus(a,b));annotation=a if consensus else j
        ok=bool(a and b and approved_source(annotation) and (consensus or j))
        decisions.append({'frame_id':ident,'approved':ok,'A':a,'B':b,'J':j,'annotation':annotation if ok else None})
    immutable_json(DATA/'review/recovered_combined_source_decisions.json',decisions)
    print('Combined source approvals',sum(d['approved'] for d in decisions),flush=True)

if __name__=='__main__':recover();reassemble()
