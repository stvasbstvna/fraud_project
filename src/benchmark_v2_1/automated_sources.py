"""Expand/screen source families and select a machine-reviewed balanced cohort."""
from __future__ import annotations
from collections import Counter,deque
from datetime import datetime,timezone
import json
import hashlib
import pandas as pd
from .core import ROOT,DATA,RESULTS,unsafe,defang,write_json,digest
from .automated_io import write_csv
from .pilot_sources import english_screen,FINANCE,BRANDS,banking_control,entity_hint
from .pilot_templates import assign_families
from .automated_protocol import AUTO_DATA,AUTO_RESULTS,SOURCE_PROMPT,SOURCE_SCHEMA,ADJ_SOURCE_PROMPT,ADJ_SOURCE_SCHEMA
from .automated_runtime import concurrent_map
from .automated_review import source_payload,source_good,source_decision


def balanced_cohort(frames,target_per_label=24):
    """Exact maximum balanced flow with source capacity <= half the cohort."""
    if frames.empty:return frames.copy()
    if not frames.frame_id.is_unique or not frames.template_family_id.is_unique:raise ValueError('One approved source per family required')
    labels=['phishing_scam','legitimate'];groups=frames.groupby(['true_label','source_id'])
    counts=groups.size().to_dict();sources=sorted(frames.source_id.unique());upper=min(target_per_label,*(int(frames.true_label.eq(x).sum()) for x in labels))
    for k in range(upper,0,-1):
        residual={};neighbors={}
        def edge(a,b,cap):
            residual[a,b]=cap;residual[b,a]=0;neighbors.setdefault(a,[]).append(b);neighbors.setdefault(b,[]).append(a)
        for label in labels:
            edge('START','LABEL:'+label,k)
            for source in sources:edge('LABEL:'+label,'SOURCE:'+source,counts.get((label,source),0))
        for source in sources:edge('SOURCE:'+source,'END',k)
        flow=0
        while True:
            parent={'START':None};queue=deque(['START'])
            while queue and 'END' not in parent:
                a=queue.popleft()
                for b in sorted(neighbors[a]):
                    if b not in parent and residual[a,b]>0:parent[b]=a;queue.append(b)
            if 'END' not in parent:break
            path=[];b='END'
            while parent[b] is not None:path.append((parent[b],b));b=parent[b]
            amount=min(residual[a,b] for a,b in path)
            for a,b in path:residual[a,b]-=amount;residual[b,a]+=amount
            flow+=amount
        if flow!=2*k:continue
        chosen=[];entity_counts=Counter();category_counts=Counter()
        for label in labels:
            for source in sources:
                need=counts.get((label,source),0)-residual['LABEL:'+label,'SOURCE:'+source]
                options=frames[frames.true_label.eq(label)&frames.source_id.eq(source)].to_dict('records')
                for _ in range(need):
                    r=min(options,key=lambda r:(entity_counts[str(r.get('entity','')).casefold()],category_counts[r.get('intent_category','')],r['frame_id']))
                    chosen.append(r);options.remove(r);entity_counts[str(r.get('entity','')).casefold()]+=1;category_counts[r.get('intent_category','')]+=1
        result=pd.DataFrame(chosen,columns=frames.columns)
        assert len(result)==2*k and result.source_id.value_counts().max()<=k
        return result.sort_values(['true_label','frame_id']).reset_index(drop=True)
    return frames.iloc[:0].copy()


def deterministic_errors(row,contaminated_families):
    errors=[];text=str(row.get('safe_text') or row.get('defanged_text',''))
    if row.get('channel')!='sms':errors.append('not_sms')
    if not english_screen(text):errors.append('English_screen_failed')
    if not (20<=len(text)<=700):errors.append('not_SMS_like_length')
    if unsafe(text):errors.append('unsafe_endpoint')
    if '\ufffd' in text:errors.append('source_encoding_damage')
    if row.get('candidate_label') not in ['phishing_scam','legitimate']:errors.append('spam_or_unknown_label')
    if row.get('candidate_label')=='legitimate' and row.get('source_id')!='SYNTH-V21' and not banking_control(text):errors.append('not_bank_notification_control')
    if row.get('license_status') not in ['CC_BY_4_0','MIT_repository','verified']:errors.append('license_HOLD')
    if row.get('source_id')=='SYNTH-V21' and row.get('candidate_label')!='legitimate':errors.append('legacy_malicious_intent_unestablished')
    if not all(str(row.get(k,'')).strip() for k in ['source_id','source_row_id','original_dataset','original_url','label_source']):errors.append('provenance_missing')
    if row.get('template_family_id') in contaminated_families:errors.append('train_validation_family_overlap')
    if str(row.get('selection_eligible','')).lower()!='true':errors.append('prior_source_screen_failed')
    return sorted(set(errors))


def _review_row(row,client):
    payload=source_payload(row)
    a=client.call('llm_reviewer_A',SOURCE_PROMPT,payload,SOURCE_SCHEMA)
    b=client.call('llm_reviewer_B',SOURCE_PROMPT,payload,SOURCE_SCHEMA)
    decision=source_decision(a['output'],b['output']);j=None
    if decision['needs_adjudication']:
        j=client.call('llm_adjudicator',ADJ_SOURCE_PROMPT,{'source':payload,'review_A':a['output'],'review_B':b['output']},ADJ_SOURCE_SCHEMA)
        decision=source_decision(a['output'],b['output'],j['output'])
    annotation=decision.get('annotation');errors=[]
    if annotation:
        entity=annotation.get('entity','NONE');destination=annotation.get('destination','NONE')
        if entity!='NONE' and entity not in row['safe_text']:errors.append('annotated_entity_not_literal')
        import re
        targets=re.findall(r'\[[^\]]+\]',destination) if destination!='NONE' else []
        if destination!='NONE' and not targets and destination not in row['safe_text']:errors.append('annotated_destination_not_literal')
        if any(x not in row['safe_text'] for x in targets):errors.append('annotated_destination_not_literal')
        if errors:decision.update(approved=False,reason=';'.join(errors))
    return row,a,b,j,decision


def prepare_sources(config):
    pool=pd.read_csv(DATA/'source/pilot_audited_candidate_pool.csv',keep_default_na=False)
    # Inspect other registered, locally available SMS controls without silently
    # promoting unresolved row-level rights to permission or using detector output.
    local=pd.read_csv(ROOT/'data/processed/unified_text_messages.csv',keep_default_na=False)
    smishx=local[local.source_dataset.eq('SmishX')&local.label.eq('legitimate')]
    extra=[]
    for r in smishx.to_dict('records'):
        if not FINANCE.search(r['text']):continue
        try:text=defang(r['text'])
        except ValueError:continue
        extra.append({'frame_id':'AUTO-SMX-'+digest(r['id'])[:20],'source_id':'SMISHX','source_row_id':r['id'],
            'original_dataset':'SmishX','original_url':'https://github.com/yizhu-joy/SmishX','label_source':'original local SmishX legitimate label',
            'raw_label':'legitimate','candidate_label':'legitimate','safe_text':text,'defanged_text':text,
            'entity':entity_hint(text),'license_status':'HOLD_upstream_rights','channel':'sms','selection_eligible':False,
            'exclusion_reason':'license/provenance/contamination review unresolved'})
    pool=pd.concat([pool,pd.DataFrame(extra)],ignore_index=True).fillna('')
    pool['safe_text']=pool.defanged_text
    pool=assign_families(pool)
    contaminated=set(pool.loc[pool.exclusion_reason.astype(str).str.contains('train_or_validation_template_overlap'),'template_family_id'])
    rule_records=[];eligible=[]
    for r in pool.to_dict('records'):
        errors=deterministic_errors(r,contaminated)
        rule_records.append({'frame_id':r['frame_id'],'review_mode':'automated','reviewer_type':'rule_based','review_stage':'source',
            'review_status':'rejected' if errors else 'approved','final_approved':False,'model':'NONE','request_hash':'',
            'assessment_json':json.dumps({'passed':not errors,'errors':errors}), 'reason':';'.join(errors)})
        if not errors:eligible.append(r)
    # Inspect every candidate control family, not just the five previously selected.
    unique={}
    for r in sorted(eligible,key=lambda r:(0 if r['candidate_label']=='legitimate' else 1,r['source_id']=='SYNTH-V21',r['frame_id'])):
        unique.setdefault(r['template_family_id'],r)
    candidates=list(unique.values())
    controls=[r for r in candidates if r['candidate_label']=='legitimate']
    prior=set(pd.read_csv(DATA/'source/pilot_48_candidates.csv').frame_id)
    positives=sorted([r for r in candidates if r['candidate_label']=='phishing_scam'],key=lambda r:(r['frame_id'] not in prior,r['frame_id']))
    jobs=controls+positives[:24]
    # Export the exact outbound allowlist for permission/privacy inspection.
    allowed={'MENDELEY-SMISH','SMS-GATEWAY','UCI-SMS','SYNTH-V21'}
    if any(r['source_id'] not in allowed for r in jobs):raise ValueError('Outbound source is not public/project-authored allowlist')
    if any(unsafe(r['safe_text']) for r in jobs):raise ValueError('Outbound text has an operational endpoint')
    packets=[source_payload(r) for r in jobs]
    proof={'destination':'https://api.openai.com/v1/responses','purpose':'user-requested automated semantic source review',
        'packet_rows':len(packets),'packet_sources':dict(Counter(r['source_id'] for r in jobs)),
        'public_sources':['Mendeley DOI 10.17632/f45bkkt8pr.1 CC BY 4.0, publisher archive SHA verified',
            'wspr-ncsu/sms-phishing pinned public MIT repository, full notice retained','UCI DOI 10.24432/C5CC84 CC BY 4.0'],
        'synthetic_source':'existing project-authored fictional-bank templates, not private customer messages',
        'excluded':'all held sources, private review fields, keys, headers, detector predictions/features and raw endpoints',
        'safety_screen_passed':True,'fields':list(packets[0]) if packets else [],
        'user_authorization':'User explicitly requested LLM Reviewer A and B for each existing safe/defanged candidate and provenance, followed by API-backed generation and automated review; no human intervention requested.',
        'max_initial_source_model_calls':len(jobs)*3,'models':config['roles']}
    packet_path=AUTO_DATA/'source_review_packet.json'
    if not packet_path.exists():
        write_json(packet_path,packets);proof['packet_sha256']=hashlib.sha256(packet_path.read_bytes()).hexdigest()
        write_json(AUTO_RESULTS/'outbound_source_packet_manifest.json',proof)
    else:
        if json.loads(packet_path.read_text(encoding='utf-8'))!=packets:raise ValueError('Prepared outbound packet changed')
    return pool,extra,rule_records,controls,positives,jobs


def run_sources(config,client):
    out=DATA/'source/automated_source_cohort.csv';summary_path=AUTO_RESULTS/'source_summary.json'
    if out.exists() and summary_path.exists():
        summary=json.loads(summary_path.read_text())
        if hashlib.sha256(out.read_bytes()).hexdigest()!=summary['source_cohort_sha256']:raise ValueError('Cached source cohort changed')
        cohort=pd.read_csv(out,keep_default_na=False)
        from .automated_evidence import verify_source_approval
        for row in cohort.to_dict('records'):verify_source_approval(row,config)
        return cohort,summary
    pool,extra,rule_records,controls,positives,jobs=prepare_sources(config)
    print(f'Automated source review: {len(controls)} distinct control families, {len(positives)} positive families; initial {len(jobs)} A/B jobs',flush=True)
    reviewed=concurrent_map(lambda r:_review_row(r,client),jobs,config['max_workers'])
    records=list(rule_records);adjudications=[];decisions=[];approved=[]
    for r,a,b,j,d in reviewed:
        for role,record in [('llm_reviewer_A',a),('llm_reviewer_B',b)]:
            records.append({'frame_id':r['frame_id'],'review_mode':'automated','reviewer_type':role,'review_stage':'source',
                'review_status':'approved' if source_good(record['output']) else 'rejected','final_approved':d['approved'],
                'model':record['model'],'request_hash':record['request_hash'],'assessment_json':json.dumps(record['output']),
                'reason':record['output']['reason']})
        if j:adjudications.append({'frame_id':r['frame_id'],'variant_id':'','stage':'source','review_mode':'automated',
            'review_status':'adjudicated','reviewer_type':'llm_adjudicator','model':j['model'],'request_hash':j['request_hash'],
            'decision':j['output']['decision'],'assessment_json':json.dumps(j['output'])})
        decisions.append({'frame_id':r['frame_id'],'review_mode':'automated','review_status':d['review_status'],
            'approved':d['approved'],'review_A_request_hash':a['request_hash'],'review_B_request_hash':b['request_hash'],
            'adjudication_request_hash':j['request_hash'] if j else '', 'reason':d.get('reason',''),
            'reviewer_label_agreement':a['output']['label_assessment']==b['output']['label_assessment']})
        if d['approved']:
            ann=d['annotation'];label={'phishing':'phishing_scam','legitimate':'legitimate'}[ann['label_assessment']]
            approved.append({**r,'original_label':r['raw_label'],'true_label':label,'channel':'sms','language':'en',
                'banking_related':'yes','intent':ann['intent'],'requested_action':ann['requested_action'],'entity':ann['entity'],
                'destination':ann['destination'],'review_mode':'automated','review_status':d['review_status'],
                'automated_source_approved':True,'source_review_A_hash':a['request_hash'],'source_review_B_hash':b['request_hash'],
                'source_adjudication_hash':j['request_hash'] if j else '', 'source_semantic_annotation':json.dumps(ann)})
    approved_frame=pd.DataFrame(approved,columns=list(approved[0]) if approved else list(pool.columns)+['true_label'])
    cohort=balanced_cohort(approved_frame)
    # Final label balance and source capacities are decided before generation.
    fields=list(records[0]);write_csv(DATA/'review/automated_source_review.csv',records,fields)
    write_csv(DATA/'review/automated_source_decisions.csv',decisions,list(decisions[0]) if decisions else ['frame_id','approved'])
    write_csv(DATA/'review/automated_adjudication_source.csv',adjudications,list(adjudications[0]) if adjudications else ['frame_id','variant_id','stage','review_mode','review_status','reviewer_type','model','request_hash','decision','assessment_json'])
    write_csv(DATA/'source/automated_audited_pool.csv',pool.to_dict('records'),list(pool.columns))
    write_csv(out,cohort.to_dict('records'),list(cohort.columns))
    summary={'review_mode':'automated','validation_type':'automated_semantic_review','initial_candidates':len(pool),
        'additional_SmishX_controls_inspected_but_HOLD':len(extra),'deterministic_rejections':sum(x['review_status']=='rejected' for x in rule_records),
        'distinct_eligible_control_families':len(controls),'distinct_eligible_positive_families':len(positives),
        'source_frames_machine_reviewed':len(reviewed),'reviewer_label_agreements':sum(x['reviewer_label_agreement'] for x in decisions),
        'reviewer_label_disagreements':sum(not x['reviewer_label_agreement'] for x in decisions),'adjudications':len(adjudications),
        'approved_before_balancing':approved_frame.true_label.value_counts().to_dict() if len(approved_frame) else {},
        'rejected_source_frames':sum(not x['approved'] for x in decisions),'final_balanced_N':len(cohort),
        'final_labels':cohort.true_label.value_counts().to_dict() if len(cohort) else {},
        'final_sources':cohort.source_id.value_counts().to_dict() if len(cohort) else {},
        'template_families':int(cohort.template_family_id.nunique()) if len(cohort) else 0,
        'timestamp_utc':datetime.now(timezone.utc).isoformat(),'source_cohort_sha256':hashlib.sha256(out.read_bytes()).hexdigest(),
        'review_models':config['roles'],'independent_human_annotation':False,
        'limitations':['Confidence is not calibrated','Machine consensus is not ground truth','Reduced N and synthetic controls limit inference']}
    write_json(summary_path,summary);print(json.dumps(summary),flush=True)
    return cohort,summary
