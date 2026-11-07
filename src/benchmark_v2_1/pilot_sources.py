"""Original-source audit. Persist defanged banking candidates and provenance, never live message endpoints."""
from __future__ import annotations
import argparse
import csv
import hashlib
import io
import json
import re
import urllib.request
import zipfile
from datetime import datetime,timezone
from pathlib import Path
import pandas as pd
from .core import DATA,RESULTS,CONFIG,digest,defang,unsafe,write_csv,write_json
from .pilot_templates import BRANDS

MENDELEY='https://data.mendeley.com/datasets/f45bkkt8pr/1'
MENDELEY_DOWNLOAD='https://data.mendeley.com/public-files/datasets/f45bkkt8pr/files/edb361de-918d-469f-9106-e84823830665/file_downloaded'
MENDELEY_SHA='9bbf3188fdad81495d8e82825648b9b63b53fc86841a3d26c02629990b233cc3'
GATEWAY_REV='a4f18cedc9909cbf8234eea3c2028080a1e95cd4'
GATEWAY='https://github.com/wspr-ncsu/sms-phishing'
UCI='https://archive.ics.uci.edu/dataset/228/sms+spam+collection'
FINANCE=re.compile(r'\bbank\b|\bbanking\b|\bdebit\b|\bcredit card\b|\btransaction\b|\bneft\b|\bpayment\b|\brefund\b|\bcard.{0,20}(?:suspend|block|restrict)|\baccount.{0,20}(?:lock|restrict|suspend)',re.I)
CONTROL=re.compile(r'\b(?:neft|bank)\b.{0,100}\b(?:transaction|never asks|credited|debited|notification|statement|security reminder)\b|\b(?:transaction|payment)\b.{0,100}\b(?:credited|debited|completed|processed)\b',re.I)
CATEGORIES=[('card_suspension',r'card.{0,30}(?:suspend|block|restrict)'),('account_locked',r'(?:lock|restrict|suspend)'),
 ('identity_verification',r'(?:identity|identification|verify|verification)'),('refund',r'refund'),
 ('fraud_alert',r'fraud|scam'),('suspicious_activity',r'suspicious|unusual|unrecognized'),
 ('transaction_alert',r'transaction|credited|debited'),('payment_issue',r'payment|declined'),
 ('login_security',r'login|log in|security|password|pin'),('account_review',r'account|review')]


def fetch(url):
    request=urllib.request.Request(url,headers={'User-Agent':'Mozilla/5.0','Accept':'*/*'})
    with urllib.request.urlopen(request,timeout=40) as response:return response.read()


def candidate_label(raw):
    return {'smishing':'phishing_scam','phishing':'phishing_scam','ham':'legitimate','legitimate':'legitimate'}.get(str(raw).strip().casefold())


def parse_gateway(content):
    rows=list(csv.reader(io.StringIO(content.decode('utf-8-sig'))))
    expected=['messageID','objectID','destination number','message','time','error in time']
    if not rows or rows[0]!=expected:raise ValueError('Unrecognized Gateway header')
    # All 68,029 rows in the pinned release have an additional metadata value
    # after message. pandas infers an index and silently shifts every named field.
    # Read only the explicitly verified first four ordinal fields; do not assign
    # invented meanings to the three trailing metadata values.
    if any(len(r)!=7 for r in rows[1:]):raise ValueError('Gateway row width differs from audited seven-field release')
    if len({r[0] for r in rows[1:]})!=len(rows)-1:raise ValueError('Duplicate Gateway messageID')
    return [{'row_id':r[0],'text':r[3],'label':'phishing'} for r in rows[1:]]


def banking_control(text):return bool(CONTROL.search(str(text)))


def english_screen(text):
    letters=[c for c in str(text) if c.isalpha()]
    return bool(letters) and sum(c.isascii() for c in letters)/len(letters)>=.95 and len(re.findall(r'\b(?:your|you|the|to|is|has|have|for|please|never|with|from|on)\b',str(text),re.I))>=2


def category(text):
    return next((name for name,pattern in CATEGORIES if re.search(pattern,text,re.I)),'other_financial')


def entity_hint(text):
    found=next((name for name in sorted(BRANDS,key=lambda x:(-len(x),x)) if re.search(r'\b'+re.escape(name)+r'\b',text,re.I)),None)
    if found:
        match=re.search(re.escape(found),text,re.I);return match.group()
    match=re.search(r'\b[A-Z][A-Za-z]+(?: [A-Z][A-Za-z]+){0,2} Bank\b',text)
    return match.group() if match else ''


def prepare_rows(source,records,source_meta):
    rows=[];counts={'input_rows':len(records),'labels':{},'financial_keyword_rows':0,'unsafe_held':0}
    for ordinal,raw in enumerate(records,1):
        text=str(raw['text']);label=raw['label'];key=str(label).strip().casefold()
        counts['labels'][key]=counts['labels'].get(key,0)+1
        if not (FINANCE.search(text) or any(re.search(r'\b'+re.escape(b)+r'\b',text,re.I) for b in BRANDS)):continue
        counts['financial_keyword_rows']+=1
        try:safe=defang(text)
        except ValueError:counts['unsafe_held']+=1;continue
        # Dataset HTML masks and long numeric reference/account identifiers stay non-operational.
        safe=re.sub(r'&lt;[^;]+?&gt;|<[^>]+>','[SOURCE-MASK]',safe)
        safe=re.sub(r'(?<![\w.])\d{6,}(?![\w.])','[SAFE-IDENTIFIER]',safe)
        mapped=candidate_label(label);screen=english_screen(safe)
        control=banking_control(safe)
        reason=[]
        if mapped is None:reason.append('spam_or_unknown_not_phishing_ground_truth')
        if mapped=='legitimate' and not control:reason.append('not_a_bank_origin_notification_control')
        if not screen:reason.append('English_screen_failed')
        if len(safe)>700 or len(safe)<20:reason.append('not_SMS_like_length')
        if '\ufffd' in safe:reason.append('source_encoding_damage')
        if unsafe(safe):reason.append('unresolved_endpoint')
        row_id=str(raw.get('row_id',ordinal));fid='P48-'+digest(source+'\n'+row_id+'\n'+digest(text))[:24]
        rows.append({'frame_id':fid,'source_id':source,'source_row_id':row_id,
            'source_dataset':source_meta['original_dataset'],'source_url':source_meta['original_url'],
            'aggregator':'SMISH_DT_discovery_only; downloaded_original','original_dataset':source_meta['original_dataset'],
            'original_url':source_meta['original_url'],'license_status':source_meta['license_status'],
            'label_source':'original source annotation '+str(label)+'; not independently validated',
            'raw_label':str(label),'candidate_label':mapped or 'unknown','true_label':'',
            'channel':'sms','language':'en_screened_pending_human' if screen else 'unknown',
            'banking_related':'candidate','defanged_text':safe,'safe_text':safe,
            'original_text_sha256':digest(text),'entity':entity_hint(safe),'intent':'',
            'intent_category':category(safe),'requested_action':'','destination':'',
            'provenance_status':'original_download_hash_recorded','review_status':'pending',
            'source_validated':'pending','label_validated':'pending','selection_eligible':not reason,
            'exclusion_reason':';'.join(reason),'source_snapshot_sha256':source_meta['sha256'],
            'source_version':source_meta['version'],'notes':'Automated candidate triage only; Stage A must supply controlled semantics; no detector scores'})
    return rows,counts


def main():
    p=argparse.ArgumentParser();p.add_argument('--offline',action='store_true');a=p.parse_args()
    if a.offline:raise SystemExit('Original-source retrieval requires network; use saved pilot_external_audit_rows.csv downstream')
    all_rows=[];audit={'timestamp_utc':datetime.now(timezone.utc).isoformat(),'sources':[],'api_generation_calls':0}
    m=fetch(MENDELEY_DOWNLOAD)
    if hashlib.sha256(m).hexdigest()!=MENDELEY_SHA:raise ValueError('Publisher archive hash mismatch')
    archive=zipfile.ZipFile(io.BytesIO(m));raw=archive.read('Dataset_5971.csv')
    for encoding in ['utf-8-sig','cp1252']:
        try:df=pd.read_csv(io.BytesIO(raw),encoding=encoding);break
        except UnicodeDecodeError:continue
    meta={'source_id':'MENDELEY-SMISH','original_dataset':'Mishra and Soni SMS Phishing Dataset v1','original_url':MENDELEY,
        'license_status':'CC_BY_4_0','version':'1','sha256':MENDELEY_SHA,'download_url':MENDELEY_DOWNLOAD,
        'archive_member_sha256':hashlib.sha256(raw).hexdigest(),'encoding':encoding,
        'attribution':'Mishra S.; Soni D. (2022). DOI 10.17632/f45bkkt8pr.1. Safe redactions and candidate filtering are project modifications.'}
    rows,counts=prepare_rows('MENDELEY-SMISH',[{'text':r.TEXT,'label':r.LABEL,'row_id':i+1} for i,r in df.iterrows()],meta)
    all_rows+=rows;audit['sources'].append({**meta,**counts,'decision':'CANDIDATES_ONLY_PENDING_SOURCE_REVIEW'})
    base=f'https://raw.githubusercontent.com/wspr-ncsu/sms-phishing/{GATEWAY_REV}/'
    license_text=fetch(base+'LICENSE').decode();readme=fetch(base+'README.md').decode();content=fetch(base+'phishing_messages.csv')
    if 'MIT License' not in license_text or 'phishing_messages' not in readme:raise ValueError('Gateway license/provenance changed')
    gateway_records=parse_gateway(content)
    meta={'source_id':'SMS-GATEWAY','original_dataset':'On SMS Phishing Tactics and Infrastructure','original_url':GATEWAY,
        'license_status':'MIT_repository','version':GATEWAY_REV,'sha256':hashlib.sha256(content).hexdigest(),
        'download_url':base+'phishing_messages.csv','label_limitation':'README uses VirusTotal/APWG flags; not human message ground truth',
        'schema_note':'Header has six names but rows have seven fields; first four ordinal fields verified; trailing metadata not interpreted; no pandas implicit index',
        'attribution':'Nahapetyan et al., IEEE S&P 2024; Copyright (c) 2023 wspr-ncsu; MIT license retained.'}
    rows,counts=prepare_rows('SMS-GATEWAY',gateway_records,meta)
    all_rows+=rows;audit['sources'].append({**meta,**counts,'decision':'CANDIDATES_ONLY_PENDING_MESSAGE_LABEL_REVIEW'})
    for filename,text in [('pilot_gateway_LICENSE.txt',license_text),('pilot_gateway_README.txt',readme)]:
        with (DATA/'source'/filename).open('x',encoding='utf-8') as handle:handle.write(text)
    u=fetch('https://archive.ics.uci.edu/static/public/228/sms+spam+collection.zip');z=zipfile.ZipFile(io.BytesIO(u))
    lines=z.read('SMSSpamCollection').decode('utf-8').splitlines()
    records=[{'text':parts[1],'label':parts[0],'row_id':i+1} for i,line in enumerate(lines) if len(parts:=line.split('\t',1))==2]
    meta={'source_id':'UCI-SMS','original_dataset':'UCI SMS Spam Collection','original_url':UCI,'license_status':'CC_BY_4_0',
        'version':'original_archive','sha256':hashlib.sha256(u).hexdigest(),'download_url':'https://archive.ics.uci.edu/static/public/228/sms+spam+collection.zip',
        'attribution':'Almeida T.; Hidalgo J. (2011). UCI SMS Spam Collection. DOI 10.24432/C5CC84. Modified by safe redaction.'}
    rows,counts=prepare_rows('UCI-SMS',records,meta)
    # UCI is evaluated for legitimate controls only; even its spam is never a phishing candidate.
    for r in rows:
        if r['candidate_label']!='legitimate':r.update(selection_eligible=False,exclusion_reason='UCI_controls_only')
    all_rows+=rows;audit['sources'].append({**meta,**counts,'decision':'BANK_NOTIFICATION_CONTROLS_ONLY_PENDING_REVIEW'})
    registry=pd.read_csv(CONFIG/'source_registry.csv',keep_default_na=False)
    for sid in ['SMISHTANK','SMISHX','SPAMHUNTER','SUPER-SMS']:
        r=registry[registry.source_id.eq(sid)].iloc[0]
        audit['sources'].append({'source_id':sid,'decision':'HOLD','original_url':r.original_url,
            'reason':'unresolved row-level rights/label provenance or training overlap; no new rows selected; previous registry evidence retained'})
    write_csv(DATA/'source/pilot_external_audit_rows.csv',all_rows,list(all_rows[0]))
    write_json(RESULTS/'diagnostics/pilot_original_source_audit.json',audit)
    print(json.dumps({'audit_candidate_rows':len(all_rows),'source_counts':{r['source_id']:r.get('input_rows') for r in audit['sources']},'human_approvals':0}))


if __name__=='__main__':main()
