from pathlib import Path
from datetime import datetime, timezone
from collections import Counter, defaultdict
import hashlib
import json
import csv
import re

ROOT=Path(__file__).resolve().parents[2]
DATA=ROOT/'data/benchmark_v3_2'
RESULTS=ROOT/'results/benchmark_v3_2'
CONFIG=ROOT/'configs/benchmark_v3_2'
DOCS=ROOT/'docs/benchmark_v3_2'
MODELS=ROOT/'models/benchmark_v3_2'
CONDITIONS=['C0','C1','C4','C5','C6']
ROLES={'G':'gpt-5.4-mini-2026-03-17','A':'gpt-5.4-mini-2026-03-17','B':'gpt-4.1-mini-2025-04-14','J':'gpt-4.1-2025-04-14'}
GATES=['same_intent','same_requested_action','same_institution_entity','same_destination','same_event','same_label','no_new_facts','safe','condition_followed','meaningfully_changed','natural_language']

def now(): return datetime.now(timezone.utc).isoformat()
def sha(value): return hashlib.sha256(value if isinstance(value,bytes) else str(value).encode('utf-8')).hexdigest()
def file_sha(path):
    with Path(path).open('rb') as f: return hashlib.file_digest(f,'sha256').hexdigest()
def canonical(value): return json.dumps(value,sort_keys=True,ensure_ascii=False)
def read(path): return json.loads(Path(path).read_text(encoding='utf-8'))
def immutable_bytes(path,value):
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
    if path.exists():
        if path.read_bytes()!=value: raise ValueError('Immutable output already differs: '+str(path))
        return
    with path.open('xb') as f:f.write(value)
def immutable_json(path,value): immutable_bytes(path,(json.dumps(value,indent=2,ensure_ascii=False,sort_keys=True)+'\n').encode('utf-8'))
def immutable_text(path,value): immutable_bytes(path,value.encode('utf-8'))
def csv_rows(path):
    with Path(path).open(encoding='utf-8-sig',newline='') as f:return list(csv.DictReader(f))
def write_csv(path,rows,fields=None):
    import io
    fields=fields or (list(rows[0]) if rows else ['status'])
    s=io.StringIO(newline='');w=csv.DictWriter(s,fieldnames=fields,extrasaction='raise');w.writeheader();w.writerows(rows)
    immutable_text(path,s.getvalue())
def blind(obj):
    if isinstance(obj,dict):
        for k,v in obj.items():
            if re.search(r'probabil|predict|logit|detector|score|tfidf|distance',k,re.I):raise ValueError('Detector or measured-distance feedback forbidden: '+k)
            blind(v)
    elif isinstance(obj,list):
        for v in obj:blind(v)
def complete_ids(rows):
    seen=defaultdict(set)
    for r in rows:
        if r['condition'] in seen[r['frame_id']]:raise ValueError('Duplicate frame condition')
        seen[r['frame_id']].add(r['condition'])
    return {k for k,v in seen.items() if v==set(CONDITIONS)}
def retry_allowed(attempt,errors):
    return attempt==0 and bool(errors) and set(errors)<= {'unchanged','malformed','placeholders','numbers','institution','c1_insufficient_lexical_change','live_destination','semantic_failure'}
def approved_source(a):
    return bool(a and a.get('banking_related') is True and a.get('label') in {'phishing','legitimate'} and a.get('language','').casefold() in {'en','english'} and a.get('channel','').casefold()=='sms' and a.get('safe') is True and .8<=a.get('confidence',-1)<=1 and a.get('decision')=='approve')
def approved_rewrite(a):return bool(a and all(a.get(k) is True for k in GATES) and .8<=a.get('confidence',-1)<=1)
def source_consensus(a,b):
    return approved_source(a) and approved_source(b) and all(a[k]==b[k] for k in ['label','intent','requested_action','institution_entity','destination','message_function','event_or_claim'])

def verify_protected():
    inv=csv_rows(DATA/'provenance/protected_inventory.csv')
    for r in inv:
        if not (ROOT/r['path']).is_file() or file_sha(ROOT/r['path'])!=r['sha256']:raise ValueError('Protected historical file changed: '+r['path'])
    return len(inv)
