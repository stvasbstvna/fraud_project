"""Execute one fixed rewrite per condition, then independent machine review."""
from __future__ import annotations
from datetime import datetime,timezone
import hashlib
import json
import pandas as pd
from .core import DATA,CONFIG,write_json,generation_payload,digest
from .automated_io import write_csv
from .automated_protocol import (AUTO_DATA,AUTO_RESULTS,REWRITE_PROMPT,REWRITE_SCHEMA,
    ADJ_REWRITE_PROMPT,PAIR_PROMPT,PAIR_SCHEMA)
from .automated_runtime import concurrent_map
from .automated_review import rewrite_errors,rewrite_good,rewrite_decision
from .automated_sources import balanced_cohort


def _generate(row,client,config):
    condition=row['condition'];path=CONFIG/'prompts'/config['generation_prompt_files'][condition]
    prompt=path.read_text(encoding='utf-8')
    if digest(prompt)!=config['generation_prompt_hashes'][condition]:raise ValueError('Generation prompt changed')
    response=client.call('generator',prompt,generation_payload(row),config['generation_schema'],generation=True)
    parsed=response['output']
    if parsed['frame_id']!=row['frame_id'] or parsed['condition']!=condition:raise ValueError('Generated response identity changed')
    return {**row,'variant_text':parsed['text'],'generation_status':'completed','generation_model':response['model'],
        'generation_provider':'OpenAI','generation_attempt':response['attempt'],'generation_request_hash':response['request_hash'],
        'generation_prompt_hash':response['prompt_sha256'],'prompt_version':config['generation_prompt_version'],
        'generation_response_id':response['response_id'],'generated_at_utc':response['timestamp_utc']}


def _review(row,client,config):
    errors=rewrite_errors(row)
    if errors:return row,None,None,None,{'review_mode':'automated','approved':False,'review_status':'rejected','reason':';'.join(errors)}
    payload={k:row[k] for k in ['frame_id','condition','true_label','defanged_text','variant_text','intent','requested_action','entity','destination']}
    payload['condition_instruction']=(CONFIG/'prompts'/config['generation_prompt_files'][row['condition']]).read_text(encoding='utf-8')
    a=client.call('llm_reviewer_A',REWRITE_PROMPT,payload,REWRITE_SCHEMA)
    b=client.call('llm_reviewer_B',REWRITE_PROMPT,payload,REWRITE_SCHEMA)
    d=rewrite_decision(a['output'],b['output']);j=None
    if d['needs_adjudication']:
        j=client.call('llm_adjudicator',ADJ_REWRITE_PROMPT,{'variant':payload,'review_A':a['output'],'review_B':b['output']},REWRITE_SCHEMA)
        d=rewrite_decision(a['output'],b['output'],j['output'])
    return row,a,b,j,d


def run_generation(cohort,config,client):
    matrix_path=AUTO_DATA/'reviewed_matrix.csv'
    summary_path=AUTO_RESULTS/'rewrite_summary.json'
    if matrix_path.exists() and summary_path.exists():return pd.read_csv(matrix_path,keep_default_na=False),json.loads(summary_path.read_text())
    if cohort.empty:raise ValueError('No balanced machine-approved sources')
    if not cohort.automated_source_approved.astype(str).str.lower().eq('true').all():raise ValueError('Unapproved automated source')
    baseline=[];jobs=[]
    for source in cohort.to_dict('records'):
        for i in range(7):
            row={**source,'condition':f'C{i}','variant_id':f"{source['frame_id']}-C{i}",
                'defanged_text':source['safe_text'],'original_text':source['safe_text'],'variant_text':'',
                'review_mode':'automated','automated_rewrite_approved':False,'human_review_status':'not_applicable_automated',
                'rewrite_A_hash':'','rewrite_B_hash':'','rewrite_adjudication_hash':'','generation_request_hash':'',
                'pilot_complete_case':False}
            if i==0:
                row.update(variant_text=source['safe_text'],generation_status='not_applicable',
                    automated_rewrite_approved=True,rewrite_review_status='approved',
                    rewrite_review_type='C0_identity_and_machine_source_review')
                baseline.append(row)
            else:jobs.append(row)
    print(f'Generating {len(jobs)} actual C1–C6 variants, no C0 generation',flush=True)
    generated=concurrent_map(lambda row:_generate(row,client,config),jobs,config['max_workers'])
    write_csv(AUTO_DATA/'generated_variants.csv',generated,list(generated[0]))
    print(f'{len(generated)} generated; starting deterministic and isolated A/B semantic review',flush=True)
    reviewed=concurrent_map(lambda row:_review(row,client,config),generated,config['max_workers'])
    records=[];adjudications=[];rows=list(baseline);accepted=0;disagreed=0;deterministic_rejected=0
    for row,a,b,j,d in reviewed:
        errors=rewrite_errors(row)
        records.append({'frame_id':row['frame_id'],'variant_id':row['variant_id'],'condition':row['condition'],
            'review_mode':'automated','reviewer_type':'rule_based','review_status':'rejected' if errors else 'approved',
            'final_approved':d['approved'],'model':'NONE','request_hash':'','assessment_json':json.dumps({'errors':errors})})
        if errors:deterministic_rejected+=1
        if a:
            for role,result in [('llm_reviewer_A',a),('llm_reviewer_B',b)]:
                records.append({'frame_id':row['frame_id'],'variant_id':row['variant_id'],'condition':row['condition'],
                    'review_mode':'automated','reviewer_type':role,'review_status':'approved' if rewrite_good(result['output']) else 'rejected',
                    'final_approved':d['approved'],'model':result['model'],'request_hash':result['request_hash'],
                    'assessment_json':json.dumps(result['output'])})
            disagreed+=int(any(a['output'][k]!=b['output'][k] for k in ['same_intent','same_action','same_entity','same_destination','same_label','condition_followed','new_facts','natural_language','safe']))
        if j:
            adjudications.append({'frame_id':row['frame_id'],'variant_id':row['variant_id'],'stage':'rewrite','review_mode':'automated',
                'review_status':'adjudicated','reviewer_type':'llm_adjudicator','model':j['model'],'request_hash':j['request_hash'],
                'decision':'approve' if d['approved'] else 'reject','assessment_json':json.dumps(j['output'])})
        rows.append({**row,'automated_rewrite_approved':d['approved'],'rewrite_review_status':d['review_status'],
            'rewrite_review_type':'automated_semantic_review','rewrite_A_hash':a['request_hash'] if a else '',
            'rewrite_B_hash':b['request_hash'] if b else '', 'rewrite_adjudication_hash':j['request_hash'] if j else '',
            'rewrite_rejection_reason':';'.join(errors) if errors else ('' if d['approved'] else 'machine_semantic_review_failed')})
        accepted+=int(d['approved'])
    data=pd.DataFrame(rows).fillna('')
    complete=[];attrition=[]
    for fid,g in data.groupby('frame_id'):
        rejected=g.loc[~g.automated_rewrite_approved.astype(str).str.lower().eq('true'),'condition'].tolist()
        ok=len(g)==7 and not rejected
        if ok:complete.append(fid)
        attrition.append({'frame_id':fid,'true_label':g.iloc[0].true_label,'pilot_complete_case':ok,
            'rejected_conditions':';'.join(rejected),'reason':'' if ok else 'one_or_more_required_conditions_failed'})
    data['pilot_complete_case']=data.frame_id.isin(complete)
    # Preserve all approved/rejected variants. Only complete, balanced sources
    # are frozen, without consulting any score or prediction.
    surviving_sources=cohort[cohort.frame_id.isin(complete)]
    final_sources=balanced_cohort(surviving_sources)
    final=data[data.frame_id.isin(final_sources.frame_id)].copy()
    write_csv(matrix_path,data.to_dict('records'),list(data.columns))
    write_csv(AUTO_DATA/'complete_balanced_matrix.csv',final.to_dict('records'),list(final.columns))
    write_csv(DATA/'review/automated_rewrite_review.csv',records,list(records[0]))
    source_adj=pd.read_csv(DATA/'review/automated_adjudication_source.csv',keep_default_na=False)
    merged=source_adj.to_dict('records')+adjudications
    adjfields=['frame_id','variant_id','stage','review_mode','review_status','reviewer_type','model','request_hash','decision','assessment_json']
    write_csv(DATA/'review/automated_adjudication.csv',merged,adjfields)
    write_csv(AUTO_RESULTS/'frame_attrition.csv',attrition,list(attrition[0]))
    bycondition=[{'condition':c,'generated':len(g),'approved':int(g.automated_rewrite_approved.astype(str).str.lower().eq('true').sum()),
        'rejected':int(g.automated_rewrite_approved.astype(str).str.lower().ne('true').sum())} for c,g in data[~data.condition.eq('C0')].groupby('condition')]
    write_csv(AUTO_RESULTS/'condition_attrition.csv',bycondition,list(bycondition[0]))
    summary={'review_mode':'automated','generated_variants':len(generated),'generation_technical_failures':0,
        'approved_generated_variants':accepted,'rejected_generated_variants':len(generated)-accepted,
        'deterministic_rejections':deterministic_rejected,'rewrite_reviewer_disagreements':disagreed,'rewrite_adjudications':len(adjudications),
        'starting_source_frames':len(cohort),'complete_case_frames_before_rebalance':len(complete),
        'final_complete_balanced_frames':len(final_sources),'final_condition_rows':len(final),
        'final_labels':final_sources.true_label.value_counts().to_dict() if len(final_sources) else {},
        'generated_variants_sha256':hashlib.sha256((AUTO_DATA/'generated_variants.csv').read_bytes()).hexdigest(),
        'reviewed_matrix_sha256':hashlib.sha256(matrix_path.read_bytes()).hexdigest(),
        'timestamp_utc':datetime.now(timezone.utc).isoformat(),'independent_human_annotation':False}
    write_json(summary_path,summary);print(json.dumps(summary),flush=True)
    return data,summary
