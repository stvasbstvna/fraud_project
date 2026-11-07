"""Bind machine decisions to exact role/prompt/payload/raw response and cached data hashes."""
import hashlib
import json
from pathlib import Path
import jsonschema
import pandas as pd
from .core import digest,generation_payload,CONFIG
from .automated_protocol import (AUTO_DATA,SOURCE_PROMPT,SOURCE_SCHEMA,ADJ_SOURCE_PROMPT,ADJ_SOURCE_SCHEMA,
    REWRITE_PROMPT,REWRITE_SCHEMA,ADJ_REWRITE_PROMPT)
from .automated_review import source_payload,source_decision,rewrite_decision,rewrite_errors


def expected_request(config,role,prompt,payload,schema,*,generation=False):
    return {'model':config['roles'][role],'instructions':prompt,'input':json.dumps(payload,sort_keys=True,ensure_ascii=False),
        'temperature':config['generation_temperature'] if generation else config['review_temperature'],
        'top_p':config['generation_top_p'] if generation else config['review_top_p'],
        'max_output_tokens':config['generation_max_output_tokens'] if generation else config['review_max_output_tokens'],
        'store':False,'text':{'format':{'type':'json_schema','name':'controlled_benchmark_output','strict':True,'schema':schema}}}


def verify_call(key,role,prompt,payload,schema,config,*,generation=False,calls=None):
    calls=Path(calls) if calls else AUTO_DATA/'calls'
    request=json.loads((calls/f'{key}.request.json').read_text(encoding='utf-8'))
    record=json.loads((calls/f'{key}.result.json').read_text(encoding='utf-8'))
    expected=expected_request(config,role,prompt,payload,schema,generation=generation)
    expected_hash=digest(json.dumps({'role':role,'request':expected},sort_keys=True,ensure_ascii=False))
    if expected_hash!=key or request.get('request_hash')!=key or request.get('role')!=role or request.get('raw_request')!=expected:
        raise ValueError('Provider evidence bound to wrong role/prompt/payload/request')
    if record.get('request_hash')!=key or record.get('role')!=role or record.get('model')!=config['roles'][role] or record.get('status')!='completed':
        raise ValueError('Incorrect completed provider record')
    raw=record['raw_response']
    rawtext=''.join(c.get('text','') for item in raw.get('output',[]) for c in item.get('content',[]) if c.get('type')=='output_text')
    if raw.get('id')!=record.get('response_id') or raw.get('model')!=record['model'] or json.loads(rawtext)!=record['output']:
        raise ValueError('Parsed review differs from original provider output')
    jsonschema.validate(record['output'],schema)
    return record['output']


def verify_source_approval(row,config):
    payload=source_payload(row)
    a=verify_call(row['source_review_A_hash'],'llm_reviewer_A',SOURCE_PROMPT,payload,SOURCE_SCHEMA,config)
    b=verify_call(row['source_review_B_hash'],'llm_reviewer_B',SOURCE_PROMPT,payload,SOURCE_SCHEMA,config)
    j=None
    if row.get('source_adjudication_hash'):
        j=verify_call(row['source_adjudication_hash'],'llm_adjudicator',ADJ_SOURCE_PROMPT,
            {'source':payload,'review_A':a,'review_B':b},ADJ_SOURCE_SCHEMA,config)
    decision=source_decision(a,b,j)
    if not decision['approved']:raise ValueError('Source machine evidence does not approve')
    annotation=decision['annotation']
    expected_label={'phishing':'phishing_scam','legitimate':'legitimate'}[annotation['label_assessment']]
    if row['true_label']!=expected_label or any(str(row[k])!=str(annotation[k]) for k in ['intent','requested_action','entity','destination']):
        raise ValueError('Frozen source annotations differ from actual machine decision')


def verify_variant_approval(row,config):
    verify_source_approval(row,config)
    if rewrite_errors(row):raise ValueError('Deterministic variant validation fails')
    if row['condition']=='C0':return
    prompt=(CONFIG/'prompts'/config['generation_prompt_files'][row['condition']]).read_text(encoding='utf-8')
    generated=verify_call(row['generation_request_hash'],'generator',prompt,generation_payload(row),config['generation_schema'],config,generation=True)
    if generated!={'frame_id':row['frame_id'],'condition':row['condition'],'text':row['variant_text']}:raise ValueError('Generated response identity/text changed')
    payload={k:row[k] for k in ['frame_id','condition','true_label','defanged_text','variant_text','intent','requested_action','entity','destination']}
    payload['condition_instruction']=prompt
    a=verify_call(row['rewrite_A_hash'],'llm_reviewer_A',REWRITE_PROMPT,payload,REWRITE_SCHEMA,config)
    b=verify_call(row['rewrite_B_hash'],'llm_reviewer_B',REWRITE_PROMPT,payload,REWRITE_SCHEMA,config)
    j=None
    if row.get('rewrite_adjudication_hash'):
        j=verify_call(row['rewrite_adjudication_hash'],'llm_adjudicator',ADJ_REWRITE_PROMPT,
            {'variant':payload,'review_A':a,'review_B':b},REWRITE_SCHEMA,config)
    if not rewrite_decision(a,b,j)['approved']:raise ValueError('Machine evidence rejects frozen variant')


def load_prediction_cache(path,manifest_path,frozen_sha,models):
    path=Path(path);m=json.loads(Path(manifest_path).read_text(encoding='utf-8'))
    if m.get('frozen_data_sha256')!=frozen_sha or m.get('models')!=models:raise ValueError('Evaluation cache belongs to different freeze/models')
    if hashlib.sha256(path.read_bytes()).hexdigest()!=m.get('predictions_sha256'):raise ValueError('Cached prediction data changed')
    return pd.read_csv(path,keep_default_na=False)
