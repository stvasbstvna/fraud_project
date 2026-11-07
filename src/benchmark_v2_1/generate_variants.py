"""Create exact blinded pilot requests, or ingest externally executed structured responses.

No provider request occurs in this CLI. Sources must pass review before requests
are exported; the provider/model is never silently substituted.
"""
import argparse
import json
from datetime import datetime, timezone
import jsonschema
import pandas as pd
from .core import CONFIG, DATA, VARIANT_FIELDS, build_matrix, generation_payload, source_eligible, verify_source_reviews, digest, validate_variant, write_json, write_csv


def make_requests(frames,source_reviews=None):
    config=json.loads((CONFIG/'generator_config.json').read_text(encoding='utf-8'))
    eligible=[r for r in frames.to_dict('records') if source_eligible(r)]
    if eligible:verify_source_reviews(eligible,source_reviews or [])
    requests=[]
    for row in build_matrix(frames):
        if row['condition']=='C0' or not source_eligible(row):continue
        condition=row['condition']; path=CONFIG/'prompts'/config['prompt_files'][condition]
        prompt=path.read_text(encoding='utf-8')
        payload=generation_payload(row)
        request={'variant_id':row['variant_id'],'provider':config['provider'],'model':config['exact_model_version'],
                 'api_type':config['api_type'],'temperature':config['temperature'],'top_p':config['top_p'],
                 'max_output_tokens':config['max_output_tokens'],'prompt_version':config['prompt_version'],
                 'prompt':prompt,'payload':payload,'structured_output_schema':config['structured_output_schema'],
                 'prompt_sha256':digest(prompt)}
        request['request_sha256']=digest(json.dumps(request,sort_keys=True,ensure_ascii=False))
        requests.append(request)
    return requests


def verify_response(row,request,envelope,config):
    required=['request_sha256','model','provider','attempt','response_id','timestamp_utc','output']
    if any(k not in envelope or envelope[k] in ('',None) for k in required):raise ValueError('Missing raw response evidence')
    for field in ['request_sha256','model','provider']:
        if envelope[field]!=request[field]:raise ValueError('Response generator/request substituted')
    if row['variant_id']!=request['variant_id']:raise ValueError('Variant identity mismatch')
    for field in ['request_sha256','prompt_sha256','prompt_version']:
        if row.get(field)!=request[field]:raise ValueError('Prompt/request metadata changed')
    if row.get('generator_model')!=request['model'] or row.get('generator_provider')!=request['provider']:
        raise ValueError('Generator metadata changed')
    attempt=int(envelope['attempt'])
    if not 1<=attempt<=config['max_attempts'] or int(row.get('generation_attempt') or 0)!=attempt:raise ValueError('Invalid generation attempt')
    if attempt==2 and not any(r.get('attempt')==1 and r.get('status')=='failed_technical' and r.get('request_sha256')==request['request_sha256'] for r in envelope.get('prior_attempts',[])):
        raise ValueError('Second attempt requires technical-failure evidence')
    stamp=datetime.fromisoformat(envelope['timestamp_utc'].replace('Z','+00:00'))
    if stamp.tzinfo is None:raise ValueError('Response timestamp requires timezone')
    if row.get('response_id')!=envelope['response_id'] or row.get('generated_at_utc')!=envelope['timestamp_utc']:
        raise ValueError('Response identity/timestamp changed')
    jsonschema.validate(envelope['output'],config['structured_output_schema'])
    output=envelope['output']
    if output['frame_id']!=row['frame_id'] or output['condition']!=row['condition'] or output['text']!=row['variant_text']:
        raise ValueError('Raw response differs from retained variant')


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--frames',default=str(DATA/'source/pilot_candidates.csv'))
    p.add_argument('--dry-run',action='store_true')
    p.add_argument('--responses',help='JSONL transport envelopes bound to request_sha256')
    p.add_argument('--source-reviews',default=str(DATA/'review/source_review_completed.csv'))
    p.add_argument('--output',default=str(DATA/'generated/pilot_responses.csv'))
    args=p.parse_args()
    from pathlib import Path
    frames=pd.read_csv(args.frames,keep_default_na=False)
    source_reviews=pd.read_csv(args.source_reviews,keep_default_na=False).to_dict('records') if Path(args.source_reviews).exists() else []
    requests=make_requests(frames,source_reviews)
    if args.dry_run:
        write_json(DATA/'generated/dry_run.json',{'status':'PENDING_SOURCE_REVIEW' if not requests else 'REQUESTS_PREPARED_NOT_EXECUTED',
            'candidate_frames':len(frames),'eligible_frames':sum(source_eligible(r) for r in frames.to_dict('records')),
            'api_calls':0,'requests':requests,'timestamp_utc':datetime.now(timezone.utc).isoformat()})
        print(f'DRY RUN: {len(requests)} eligible requests; no API calls');return
    if not args.responses:raise SystemExit('Generation pending: use --dry-run or --responses. No provider adapter is executed automatically.')
    if not requests:raise ValueError('No eligible reviewed sources')
    lookup={r['request_sha256']:r for r in requests}
    matrix={r['variant_id']:r for r in build_matrix(frames)};output=[];seen=set()
    config=json.loads((CONFIG/'generator_config.json').read_text(encoding='utf-8'))
    for line in Path(args.responses).read_text(encoding='utf-8').splitlines():
        envelope=json.loads(line); req=lookup[envelope['request_sha256']]
        if req['variant_id'] in seen:raise ValueError('Duplicate response; retain one prespecified attempt, not a selected best output')
        seen.add(req['variant_id']);parsed=envelope['output']
        jsonschema.validate(parsed,config['structured_output_schema'])
        if envelope['model']!=req['model'] or envelope['provider']!=req['provider']:raise ValueError('Generator substituted')
        if parsed['frame_id']!=req['payload']['frame_id'] or parsed['condition']!=req['payload']['condition']:raise ValueError('Response identity changed')
        attempt=int(envelope['attempt'])
        if not 1<=attempt<=config['max_attempts']:raise ValueError('Attempt outside protocol')
        row={**matrix[req['variant_id']],'variant_text':parsed['text'],'generator_provider':req['provider'],
             'generator_model':req['model'],'prompt_version':req['prompt_version'],'prompt_sha256':req['prompt_sha256'],
             'request_sha256':req['request_sha256'],'response_id':envelope['response_id'],
             'generated_at_utc':envelope['timestamp_utc'],'generation_status':'completed','generation_attempt':attempt}
        errors=validate_variant(row)
        if errors:raise ValueError(f'Invalid response: {errors}; preserve rejected raw envelope separately')
        verify_response(row,req,envelope,config)
        output.append(row)
    write_csv(Path(args.output),output,VARIANT_FIELDS)


if __name__=='__main__':main()
