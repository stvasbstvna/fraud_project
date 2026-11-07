"""Objective and machine semantic review. Never emits a human approval."""
from __future__ import annotations
import json
import re
from collections import Counter
from .core import unsafe,normalize
from .automated_protocol import THRESHOLD,REWRITE_BOOLEANS


def source_payload(row):
    fields=['frame_id','safe_text','source_id','source_row_id','original_dataset','original_url','license_status','raw_label','label_source']
    return {k:row.get(k,'') for k in fields}


def compatible(a,b):
    return all(normalize(a[k])==normalize(b[k]) for k in ['intent','requested_action','entity','destination'])


def source_good(x):
    return bool(x and x.get('banking_related') is True and x.get('safe') is True
        and x.get('label_assessment') in ['phishing','legitimate'] and x.get('semantic_confidence',0)>=THRESHOLD
        and str(x.get('requested_action','')).strip().upper() not in {'','NONE','NO ACTION'})


def source_decision(a,b,adjudication=None):
    approved=source_good(a) and source_good(b) and a['label_assessment']==b['label_assessment'] and compatible(a,b)
    same_label=a.get('label_assessment')==b.get('label_assessment')
    needs=not approved and (not same_label or (source_good(a) or source_good(b)))
    annotation=a if approved else None
    if adjudication:
        approved=(adjudication.get('decision')=='approve' and adjudication.get('true_label') in ['phishing','legitimate']
            and adjudication.get('confidence',0)>=THRESHOLD and str(adjudication.get('requested_action','')).strip().upper() not in {'','NONE','NO ACTION'})
        annotation={**adjudication,'label_assessment':adjudication.get('true_label'),'safe':True,'banking_related':True} if approved else None
    return {'review_mode':'automated','approved':bool(approved),'needs_adjudication':bool(needs and adjudication is None),
        'review_status':'adjudicated' if adjudication else ('approved' if approved else 'rejected'),
        'annotation':annotation,'reason':(adjudication or a).get('reason','')}


def rewrite_good(x):
    return bool(x and all(x.get(k) is True for k in REWRITE_BOOLEANS) and x.get('new_facts') is False and x.get('confidence',0)>=THRESHOLD)


def rewrite_decision(a,b,adjudication=None):
    approved=rewrite_good(a) and rewrite_good(b)
    keys=REWRITE_BOOLEANS+['new_facts']
    needs=not approved and any(a.get(k)!=b.get(k) for k in keys)
    if adjudication is not None:approved=rewrite_good(adjudication)
    return {'review_mode':'automated','approved':bool(approved),'needs_adjudication':bool(needs and adjudication is None),
        'review_status':'adjudicated' if adjudication else ('approved' if approved else 'rejected')}


def rewrite_errors(row):
    a=str(row['defanged_text']);b=str(row.get('variant_text',''));errors=[]
    if not b.strip():errors.append('empty_output')
    if unsafe(b):errors.append('unsafe_endpoint')
    placeholder=re.compile(r'\[[^\]]+\]')
    if Counter(placeholder.findall(a))!=Counter(placeholder.findall(b)):errors.append('placeholder_changed')
    numeric=lambda text:Counter(re.findall(r'\d+(?:\.\d+)?',placeholder.sub('',text)))
    if numeric(a)!=numeric(b):errors.append('numeric_fact_changed')
    entity=str(row.get('entity','NONE'));destination=str(row.get('destination','NONE'))
    if entity!='NONE' and entity not in b:errors.append('entity_changed')
    if destination!='NONE':
        targets=placeholder.findall(destination) or [destination]
        if any(x not in b for x in targets):errors.append('destination_changed')
    if row['condition']=='C0' and a!=b:errors.append('C0_changed')
    if row['condition']!='C0' and a==b:errors.append('unchanged_rewrite')
    return errors
