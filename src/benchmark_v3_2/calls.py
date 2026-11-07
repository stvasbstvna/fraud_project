"""Content-addressed immutable API requests; prompts always read from registered files."""
from concurrent.futures import ThreadPoolExecutor
import os
from .core import *

S={'type':'string'};B={'type':'boolean'};N={'type':'number'}
def schema(fields):
    fields={'id':S,**fields}
    return {'type':'object','properties':{'items':{'type':'array','items':{'type':'object','properties':fields,'required':list(fields),'additionalProperties':False}}},'required':['items'],'additionalProperties':False}
SOURCE_SCHEMA=schema({**{k:S for k in ['frame_id','label','intent','requested_action','institution_entity','destination','message_function','event_or_claim','language','channel','decision','reason']},'banking_related':B,'safe':B,'confidence':N})
GEN_SCHEMA=schema({'text':S})
REWRITE_SCHEMA=schema({**{k:B for k in GATES},'confidence':N,'reason':S})

def prompt_record(purpose,role,condition=''):
    registry=csv_rows(CONFIG/'PROMPT_REGISTRY.csv')
    rows=[r for r in registry if r['purpose']==purpose and r['model_role']==role and r['condition']==condition]
    if len(rows)!=1:raise ValueError('Ambiguous prompt')
    r=rows[0]
    if file_sha(ROOT/r['file_path'])!=r['sha256']:raise ValueError('Prompt changed')
    return r

def verify_record(path):
    record=read(path);req=read(Path(path).with_name(Path(path).name.replace('.response.json','.request.json')))
    if sha(canonical(req['request_payload']))!=req['request_sha256']:raise ValueError('Request changed')
    raw=record['raw_response']
    if sha(canonical(raw))!=record['response_sha256'] or record['request_sha256']!=req['request_sha256']:raise ValueError('Raw response changed')
    prompt=next(r for r in csv_rows(CONFIG/'PROMPT_REGISTRY.csv') if r['prompt_id']==req['prompt_id'])
    if prompt['sha256']!=sha(req['request_payload']['instructions']) or file_sha(ROOT/prompt['file_path'])!=prompt['sha256']:raise ValueError('Prompt/request binding')
    if raw.get('model')!=req['request_payload']['model'] or raw.get('status')!='completed':raise ValueError('Provider model/status')
    output=json.loads(''.join(c['text'] for o in raw['output'] for c in o.get('content',[]) if c.get('type')=='output_text'))
    import jsonschema
    jsonschema.validate(output,req['request_payload']['text']['format']['schema'])
    expected=[x['id'] for x in json.loads(req['request_payload']['input'])['items']]
    actual=[x['id'] for x in output['items']]
    if len(set(actual))!=len(actual) or sorted(actual)!=sorted(expected):raise ValueError('Exact batch IDs mismatch')
    return output['items'],req

class Client:
    def __init__(self,offline=False):self.offline=offline;self.client=None
    def call(self,phase,role,items,condition='',attempt=0):
        blind(items)
        p=prompt_record(phase,role,condition)
        output_schema=SOURCE_SCHEMA if phase=='source_review' else GEN_SCHEMA if phase=='generation' else REWRITE_SCHEMA
        payload={'model':ROLES[role],'instructions':(ROOT/p['file_path']).read_text(encoding='utf-8'),'input':json.dumps({'items':items},ensure_ascii=False),'temperature':0,'top_p':1,'max_output_tokens':16000,'store':False,'text':{'format':{'type':'json_schema','name':'v32_'+phase,'strict':True,'schema':output_schema}}}
        h=sha(canonical(payload));base=DATA/('generated/calls' if role=='G' else f'review/{phase}/calls');stem=base/f'{role}_{h}'
        request_path=stem.with_suffix('.request.json');response_path=stem.with_suffix('.response.json');error_path=stem.with_suffix('.error.json')
        if response_path.exists():
            try:
                rows,req=verify_record(response_path)
                return [r|{'evidence_request_sha256':h,'review_model':ROLES[role],'review_prompt_version':p['prompt_id'],'review_timestamp':req['timestamp']} for r in rows]
            except Exception:
                if error_path.exists():return []
                raise
        if request_path.exists():
            # Never automatically repeat an interrupted/failed billed request.
            if error_path.exists():return []
            raise ValueError('Pending request without receipt; inspect before retry')
        if self.offline:raise ValueError('Missing offline call')
        req={'call_id':h,'run_id':read(CONFIG/'protocol.json')['run_id'],'phase':phase,'role':role,'condition':condition,'attempt':attempt,'prompt_id':p['prompt_id'],'prompt_sha256':p['sha256'],'generator_config_hash':file_sha(CONFIG/'generator_config.json'),'request_payload':payload,'request_sha256':h,'timestamp':now()}
        immutable_json(request_path,req)
        if self.client is None:
            from openai import OpenAI
            from dotenv import dotenv_values
            key=os.environ.get('OPENAI_API_KEY') or dotenv_values(ROOT/'.env').get('OPENAI_API_KEY')
            if not key:raise RuntimeError('Configured API key unavailable')
            self.client=OpenAI(api_key=key,max_retries=0,timeout=240)
        try:
            response=self.client.responses.create(**payload)
            raw=response.model_dump(mode='json')
            immutable_json(response_path,{'request_sha256':h,'response_sha256':sha(canonical(raw)),'raw_response':raw,'timestamp':now()})
            rows,_=verify_record(response_path)
            return [r|{'evidence_request_sha256':h,'review_model':ROLES[role],'review_prompt_version':p['prompt_id'],'review_timestamp':req['timestamp']} for r in rows]
        except Exception as e:
            immutable_json(error_path,{'request_sha256':h,'error_type':type(e).__name__,'reason':str(e),'timestamp':now()})
            return []

def batches(client,phase,role,items,condition='',attempt=0,size=10):
    packets=[items[i:i+size] for i in range(0,len(items),size)]
    def go(batch):return client.call(phase,role,batch,condition,attempt)
    with ThreadPoolExecutor(max_workers=4) as pool:return [r for result in pool.map(go,packets) for r in result]
