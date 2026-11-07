"""Separate Stage A source decisions from Stage B rewrite preservation decisions."""
from __future__ import annotations
import argparse
import json
from collections import Counter
from datetime import datetime,timezone
from pathlib import Path
import pandas as pd
from .core import DATA,RESULTS,CONFIG,digest,unsafe,write_csv,write_json

SOURCE_CHECKS=['banking_related','source_validated','label_validated','intent_validated','action_validated',
               'entity_validated','destination_validated','channel_validated','language_validated','safe','family_validated']
SEMANTIC_FIELDS=['true_label','intent','requested_action','entity','destination','channel','safe_text']


def pilot_source_digest(row):
    fields=['frame_id','source_id','source_row_id','original_url','original_dataset','defanged_text','candidate_label','label_source','template_family_id','license_status','source_snapshot_sha256']
    return digest(json.dumps({k:str(row.get(k,'')) for k in fields},sort_keys=True,ensure_ascii=False))


def source_readiness(frames,reviews):
    accepted=[];unresolved=[];labels=[];entities=[]
    for row in frames.fillna('').to_dict('records'):
        bound=[r for r in reviews if r.get('frame_id')==row['frame_id'] and r.get('source_sha256')==pilot_source_digest(row)]
        good=(len({str(r.get('reviewer','')).strip() for r in bound}-{''})>=2 and
              all(r.get('decision')=='approved' and all(str(r.get(k,'')).casefold()=='yes' for k in SOURCE_CHECKS)
                  and all(str(r.get(k,'')).strip() for k in SEMANTIC_FIELDS)
                  and r.get('true_label') in ['phishing_scam','legitimate'] and r.get('channel')=='sms'
                  and r.get('safe_text')==row['defanged_text'] and not unsafe(r['safe_text']) for r in bound))
        # Reviewers must agree on controlled semantic annotations, not just decision.
        if good and any(len({str(r[k]) for r in bound})!=1 for k in SEMANTIC_FIELDS):good=False
        (accepted if good else unresolved).append(row['frame_id'])
        if good:
            labels.append(bound[0]['true_label']);entities.append(bound[0]['entity'].casefold())
    reviewed=len(accepted)==len(frames) and len(frames)>0
    families=(frames.get('template_family_id',pd.Series(dtype=str)).astype(str))
    valid_families=len(families)==len(frames) and families.ne('').all() and families.is_unique
    valid_selection=frames.get('selection_eligible',pd.Series(dtype=str)).astype(str).str.lower().eq('true').all()
    agreed_counts={label:labels.count(label) for label in ['phishing_scam','legitimate']}
    source_counts=Counter(frames.get('source_id',pd.Series(dtype=str)).astype(str))
    source_balance=bool(source_counts) and max(source_counts.values())<=24 and len(source_counts)>1
    entity_balance=bool(entities) and max(Counter(entities).values())<=4
    cohort_ok=(len(frames)==48 and agreed_counts=={'phishing_scam':24,'legitimate':24} and source_balance and entity_balance
               and valid_families and bool(valid_selection) and frames.frame_id.is_unique)
    return {'status':'SOURCE_REVIEW_COMPLETE' if reviewed and cohort_ok else 'PILOT NOT READY',
        'candidate_frames':len(frames),'approved_source_frames':len(accepted),'approved_frame_ids':accepted,
        'unresolved_frame_ids':unresolved,'generation_allowed':bool(reviewed and cohort_ok),
        'approved_label_counts':agreed_counts,'cohort_design_valid':bool(cohort_ok),
        'reduced_design_rule':'Reduced N requires a separately documented prospective protocol amendment; source approval alone does not authorize it',
        'reviewer_decisions':len(reviews)}


def main():
    p=argparse.ArgumentParser();p.add_argument('--reviews',type=Path);a=p.parse_args()
    frames=pd.read_csv(DATA/'source/pilot_48_candidates.csv',keep_default_na=False)
    if a.reviews:
        state=source_readiness(frames,pd.read_csv(a.reviews,keep_default_na=False).to_dict('records'))
        print(json.dumps(state,indent=2));return
    queue=[]
    for r in frames.to_dict('records'):
        for slot in [1,2]:
            queue.append({'frame_id':r['frame_id'],'source_id':r['source_id'],'source_row_id':r['source_row_id'],
                'source_sha256':pilot_source_digest(r),'reviewer_slot':slot,'candidate_label':r['candidate_label'],
                'label_source':r['label_source'],'original_url':r['original_url'],'license_status':r['license_status'],
                'template_family_id':r['template_family_id'],'safe_text':r['defanged_text'],
                **dict.fromkeys(SOURCE_CHECKS,''),'true_label':'','intent':'','requested_action':'','entity':'','destination':'',
                'channel':'sms','reviewer':'','decision':'pending','reviewer_notes':''})
    # safe_text is input evidence, not an approval. Source semantic cells stay blank.
    write_csv(DATA/'review/pilot_source_review.csv',queue,list(queue[0]) if queue else ['frame_id','decision','reviewer'])
    schema=['frame_id','variant_id','condition','text_sha256','variant_text','reviewer','decision','same_intent','same_action',
        'same_entity','same_destination','same_label','condition_followed','no_new_facts','natural_language','safe','reviewer_notes']
    write_csv(DATA/'review/pilot_rewrite_review.csv',[],schema)
    state=source_readiness(frames,[])
    # Inspect non-secret config only; credential presence is irrelevant before Stage A.
    config=json.loads((CONFIG/'generator_config.json').read_text(encoding='utf-8'))
    state.update({'timestamp_utc':datetime.now(timezone.utc).isoformat(),'generator_active':config['active'],
        'generator_model':config['exact_model_version'],'model_availability':config['model_availability'],
        'api_calls':0,'generated_variants':0,'complete_case_frames':0,'frozen_rows':0,
        'blockers':['independent Stage A source review missing','target 24/24 cohort may be incomplete',
            'generator config inactive and provider availability unverified','Stage B cannot start before actual generated texts'],
        'next_manual_action':'Two independent reviewers complete pilot_source_review.csv; adjudicate source labels/semantics and family decisions before generation'})
    write_json(RESULTS/'diagnostics/pilot_generation_readiness.json',state)
    print(json.dumps({'source_review_assignments':len(queue),'approved_sources':0,'generation_allowed':False}))


if __name__=='__main__':main()
