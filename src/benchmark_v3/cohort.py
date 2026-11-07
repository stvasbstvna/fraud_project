"""Review-bound family construction and pre-score exploratory split freeze."""
from collections import Counter, defaultdict
from difflib import SequenceMatcher
import json
import re
import numpy as np
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from .core import DATA, RESULTS, CONFIG, digest, save_csv, save_json, leakage_errors, read_json
from .semantic_review import Client, decide, payload
from src.benchmark_v2_1.pilot_sources import entity_hint
from src.benchmark_v2_1.pilot_templates import template_text, pair_similarity


def policy_veto(text):
    return bool(re.search(r'\b(?:vodafone|airtel|telco|prepaid)\b.{0,100}\b(?:balance|refill|recharg)|\bprepaid account\b',text,re.I))


def structural_text(text):
    text=re.sub(r'(?i)(registered\s+)[A-Z][A-Za-z]+(?:\s+[A-Z][A-Za-z]+)?(\s+as\s+payee)',r'\1personslot\2',text)
    text=re.sub(r'(?i)(?:\$|£|€|₹)\s*\d+(?:\.\d+)?',' amountslot ',text)
    return template_text(text,entity_hint(text))


def stratified_partition(rows):
    result=[]
    for label in ('phishing','legitimate'):
        part=sorted([r for r in rows if r['label']==label],key=lambda r:digest('42:'+r['template_family_id']))
        if len(part)<3: raise ValueError('At least three independent families per class needed for train/validation/test support')
        test=max(1,round(len(part)*.15)); validation=max(1,round(len(part)*.15))
        for i,r in enumerate(part):
            split='held_out_test' if i<test else 'validation' if i<test+validation else 'train'
            result.append(dict(r,split=split))
    return result


def validate_adjudication_item(item,a,b):
    if item.get('review_A')!=a or item.get('review_B')!=b:
        raise ValueError('Adjudication assessment chain mismatch')


def verify_review(row, decision):
    client=Client(offline=True,version='v3.1'); assessments={}
    for role,field in [('A','review_A_hash'),('B','review_B_hash'),('J','adjudication_hash')]:
        key=decision[field]
        if not key: continue
        request=read_json(DATA/f'review/calls/{key}.request.json')
        request_payload=json.loads(request['raw_request']['input'])
        candidates=[r for r in request_payload['items'] if r['id']==row['id']]
        if len(candidates)!=1 or any(candidates[0].get(k)!=v for k,v in payload(row).items()):
            raise ValueError('Source row/text/provenance differs from actual review request')
        if role=='J':validate_adjudication_item(candidates[0],assessments['A'],assessments['B'])
        record=client.call(role,request_payload)
        if record['request_hash']!=key: raise ValueError('Review role/prompt/schema binding mismatch')
        assessment=next(r for r in record['output']['items'] if r['id']==row['id'])
        if assessment!=json.loads(decision[f'{role}_json']): raise ValueError('Recorded decision does not match actual provider assessment')
        assessments[role]=assessment
    final=decide(assessments['A'],assessments['B'],assessments.get('J'),version='v3.1')
    if final['approved']!=bool(decision['approved']) or final['annotation']!=json.loads(decision['annotation_json']):
        raise ValueError('Source approval cannot be reproduced')
    return final


def families(rows):
    text=[structural_text(r['safe_text']) for r in rows]
    x=TfidfVectorizer(analyzer='char_wb',ngram_range=(3,5),lowercase=False).fit_transform(text)
    cosine=(x@x.T).toarray(); parent=list(range(len(rows))); edges=[]
    def root(i):
        while parent[i]!=i: parent[i]=parent[parent[i]];i=parent[i]
        return i
    for i,a in enumerate(text):
        for j in range(i):
            jac,structure,match=pair_similarity(a,text[j])
            if not match and cosine[i,j]>=.90:
                structure=SequenceMatcher(None,a,text[j],autojunk=False).ratio()
                match=structure>=.75
            if match:
                left,right=root(i),root(j);parent[max(left,right)]=min(left,right)
                edges.append({'left_id':rows[i]['id'],'right_id':rows[j]['id'],'jaccard':jac,'structural_similarity':structure,'character_tfidf_cosine':float(cosine[i,j])})
    groups=defaultdict(list)
    for i,row in enumerate(rows): groups[root(i)].append(row)
    kept=[];ledger=[]
    for members in groups.values():
        fid='V3-TF-'+digest('\n'.join(sorted(structural_text(r['safe_text']) for r in members)))[:20]
        conflict=len({r['label'] for r in members})>1
        representative=min(members,key=lambda r:digest('42:'+r['id']))
        origins=sorted({o['source_id'] for r in members for o in json.loads(r['origins_json'])})
        for r in members:
            ledger.append({'id':r['id'],'source_id':r['source_id'],'label':r['label'],'template_family_id':fid,
                           'family_size':len(members),'label_conflict':conflict,'representative':not conflict and r['id']==representative['id'],
                           'family_source_origins_json':json.dumps(origins)})
        if not conflict: kept.append(representative | {'template_family_id':fid,'family_source_origins_json':json.dumps(origins)})
    return kept,ledger,edges


def main():
    candidates=pd.read_csv(DATA/'candidates/permitted_financial_candidates.csv',keep_default_na=False,low_memory=False)
    lookup={r['id']:r for r in candidates.to_dict('records')}
    approved=[];attrition=[]
    for stage in ('controls','positives'):
        decisions=pd.read_csv(DATA/f'review/{stage}_v3_1_decisions.csv',keep_default_na=False).to_dict('records')
        for d in decisions:
            row=lookup[d['id']];final=verify_review(row,d)
            veto=policy_veto(row['safe_text'])
            attrition.append({'id':row['id'],'stage':stage,'machine_approved':final['approved'],'policy_veto':veto,'included_before_family':final['approved'] and not veto})
            if not final['approved'] or veto: continue
            annotation=final['annotation']
            approved.append(row | {'label':annotation['label'],'message_function':annotation['message_function'],
                'origin_type':'uncertain' if row['origin_type']=='uncertain' else 'real',
                'review_type':'automated_semantic_review_not_human','review_A_hash':d['review_A_hash'],
                'review_B_hash':d['review_B_hash'],'adjudication_hash':d['adjudication_hash']})
    save_csv(RESULTS/'diagnostics/semantic_attrition.csv',attrition)
    kept,ledger,edges=families(approved)
    save_csv(RESULTS/'diagnostics/template_families.csv',ledger)
    save_csv(RESULTS/'diagnostics/template_edges.csv',edges,['left_id','right_id','jaccard','structural_similarity','character_tfidf_cosine'])
    cohort=stratified_partition(kept)
    if leakage_errors(cohort): raise ValueError('Primary split leakage')
    source_pool=[r for r in kept if 'gateway' not in json.loads(r['family_source_origins_json'])]
    source_cohort=stratified_partition(source_pool)
    source_cohort=[dict(r,split='validation' if r['split']=='validation' else 'train') for r in source_cohort]
    source_cohort += [dict(r,split='source_test') for r in kept if 'gateway' in json.loads(r['family_source_origins_json'])]
    if leakage_errors(source_cohort): raise ValueError('Source split leakage')
    save_csv(DATA/'frozen/modeling_cohort.csv',cohort)
    save_csv(DATA/'frozen/source_holdout_cohort.csv',source_cohort)
    counts={s:dict(Counter(r['label'] for r in cohort if r['split']==s)) for s in ['train','validation','held_out_test']}
    manifest={'status':'FROZEN_EXPLORATORY_CONTROL_TARGET_NOT_MET','validation_type':'automated_semantic_review_not_independent_human',
        'cohort_sha256':digest((DATA/'frozen/modeling_cohort.csv').read_bytes()),
        'source_holdout_cohort_sha256':digest((DATA/'frozen/source_holdout_cohort.csv').read_bytes()),
        'rows':len(cohort),'labels':dict(Counter(r['label'] for r in cohort)),'sources':dict(Counter(r['source_id'] for r in cohort)),
        'origin_types':dict(Counter(r['origin_type'] for r in cohort)),'template_families':len(kept),'primary_split_counts':counts,
        'source_holdout_counts':dict(Counter(r['split'] for r in source_cohort)),
        'source_holdout_label_counts':dict(Counter(r['label'] for r in source_cohort if r['split']=='source_test')),
        'raw_machine_approved':len(approved),'template_exclusions':len(approved)-len(kept),
        'temporal_status':'NOT RUN unreliable original message timestamps; collection/submission time not substituted',
        'minimum_desired_300_per_class_met':all(sum(r['label']==label for r in cohort)>=300 for label in ['phishing','legitimate']),
        'protocol_sha256':digest((CONFIG/'experiment_protocol.json').read_bytes()),
        'source_review_protocol_sha256':digest((CONFIG/'source_review_v3_1.json').read_bytes()),
        'source_registry_sha256':digest((DATA/'provenance/source_registry.csv').read_bytes()),
        'control_limitation':'Very few independent controls; all model results exploratory, not a population benchmark',
        'robustness_status':'NOT RUN if held-out controls below predeclared10 per class'}
    save_json(DATA/'frozen/cohort_manifest.json',manifest)
    save_json(RESULTS/'diagnostics/leakage_audit.json',{'primary_family_cross_split':False,'primary_exact_cross_split':False,
         'source_family_cross_split':False,'source_holdout_gateway_not_in_train':True,'rewrites_in_train':False,
         'temporal_evaluation':'NOT RUN','test_used_for_tuning':False,'status':'PASSED_SPLIT_AUDIT_NOT_MODEL_TRAINING_AUDIT'})
    print(json.dumps(manifest,indent=2))


if __name__=='__main__':main()
