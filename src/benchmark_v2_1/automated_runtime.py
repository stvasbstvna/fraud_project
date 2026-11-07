"""Exact-model, isolated Responses calls with append-only evidence and resumable caching."""
from __future__ import annotations
import json
import os
import time
from datetime import datetime,timezone
from pathlib import Path
import jsonschema
from .core import ROOT,digest,write_json
from .automated_protocol import AUTO_DATA


class MachineClient:
    def __init__(self,config,*,offline=False):
        self.config=config;self.calls=AUTO_DATA/'calls';self.calls.mkdir(parents=True,exist_ok=True)
        if offline:
            self.client=None
            return
        from dotenv import dotenv_values
        from openai import OpenAI
        values=dotenv_values(ROOT/'.env') if (ROOT/'.env').exists() else {}
        key=os.environ.get('OPENAI_API_KEY') or values.get('OPENAI_API_KEY')
        if not key:raise RuntimeError('OPENAI_API_KEY is absent')
        self.client=OpenAI(api_key=key,max_retries=0,timeout=90.)

    def call(self,role,prompt,payload,schema,*,generation=False):
        model=self.config['roles'][role]
        request={'model':model,'instructions':prompt,'input':json.dumps(payload,sort_keys=True,ensure_ascii=False),
            'temperature':self.config['generation_temperature'] if generation else self.config['review_temperature'],
            'top_p':self.config['generation_top_p'] if generation else self.config['review_top_p'],
            'max_output_tokens':self.config['generation_max_output_tokens'] if generation else self.config['review_max_output_tokens'],
            'store':False,'text':{'format':{'type':'json_schema','name':'controlled_benchmark_output','strict':True,'schema':schema}}}
        key=digest(json.dumps({'role':role,'request':request},sort_keys=True,ensure_ascii=False))
        final=self.calls/f'{key}.result.json'
        if final.exists():
            record=json.loads(final.read_text(encoding='utf-8'))
            if record['status']!='completed':raise RuntimeError('Recorded provider failure; no silent model substitution or extra retries')
            jsonschema.validate(record['output'],schema);return record
        if self.client is None:raise RuntimeError('Offline mode: required recorded provider result is missing')
        write_json(self.calls/f'{key}.request.json',{'request_hash':key,'role':role,'raw_request':request,'seed':None,'prompt_sha256':digest(prompt)})
        for attempt in range(1,self.config['max_technical_attempts']+1):
            started=datetime.now(timezone.utc).isoformat()
            try:
                response=self.client.responses.create(**request)
                if response.model!=model:raise ValueError(f'Provider substituted model {response.model}')
                if response.status!='completed':raise ValueError(f'Incomplete provider output: {response.status}')
                parsed=json.loads(response.output_text);jsonschema.validate(parsed,schema)
                record={'status':'completed','request_hash':key,'role':role,'model':response.model,'attempt':attempt,
                    'timestamp_utc':started,'response_id':response.id,'output':parsed,'raw_response':response.model_dump(mode='json'),
                    'prompt_sha256':digest(prompt),'temperature':request['temperature'],'top_p':request['top_p'],'seed':None}
                write_json(self.calls/f'{key}.attempt_{attempt}.json',record);write_json(final,record);return record
            except Exception as exc:
                # No credentials or request authorization headers are serialized.
                failure={'status':'failed_technical','role':role,'model':model,'request_hash':key,'attempt':attempt,
                    'timestamp_utc':started,'error_type':type(exc).__name__,'http_status':getattr(exc,'status_code',None),
                    'error_code':getattr(exc,'code',None)}
                write_json(self.calls/f'{key}.attempt_{attempt}.json',failure)
                if attempt==self.config['max_technical_attempts']:
                    write_json(final,failure);raise RuntimeError(f"Provider request failed: {failure['error_type']} {failure['error_code']}") from exc
                time.sleep(1)


def concurrent_map(function,items,workers=4):
    from concurrent.futures import ThreadPoolExecutor
    with ThreadPoolExecutor(max_workers=workers) as pool:return list(pool.map(function,items))
