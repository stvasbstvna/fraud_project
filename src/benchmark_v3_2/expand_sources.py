"""Pre-generation expansion of phishing capacity; initial source evidence stays preserved."""
import argparse
import pandas as pd
from .core import *
from .sources import family_filter,validate_packet
from .calls import Client,batches

def prepare():
    pool=pd.read_csv(ROOT/'data/benchmark_v3/candidates/permitted_financial_candidates.csv',keep_default_na=False,low_memory=False).to_dict('records')
    old=csv_rows(ROOT/'data/benchmark_v3/final_run/frozen/modeling_cohort.csv')
    existing=csv_rows(DATA/'source/review_candidates.csv')
    reference=[r for r in old if r['split']!='held_out_test']+existing
    existingids={r['id'] for r in reference}
    candidates=[r for r in pool if r['id'] not in existingids and 20<=len(r['safe_text'])<=1000 and (r['source_id']=='gateway' or r.get('raw_label','').casefold() in {'phishing','smishing'})]
    candidates=sorted(candidates,key=lambda r:sha('42:'+r['id']))[:400]
    kept,ledger,edges=family_filter(candidates,reference)
    selected=sorted(kept,key=lambda r:sha('42:'+r['id']))[:200]
    write_csv(DATA/'source/additional_candidates.csv',selected,sorted({k for r in selected for k in r}))
    write_csv(DATA/'source/additional_family_screen.csv',ledger)
    packet=[{'id':r['id'],'frame_id':r['id'],'safe_text':r['safe_text'],'source_dataset':r['source_id'],'source_row_id':r['source_row_id'],'original_label':r.get('raw_label',''),'original_url':r.get('source_url','')} for r in selected]
    immutable_json(DATA/'source/additional_outbound_packet.json',packet)
    immutable_json(DATA/'provenance/additional_authorization.json',{'timestamp':now(),'rows':len(packet),'packet_sha256':file_sha(DATA/'source/additional_outbound_packet.json'),'reason':'Initial repeat-control review and fitting-family isolation left insufficient phishing trajectories as well; expand source-only phishing capacity toward preferred100 without changing prompts or checking detector outcomes','authorization':'User v3.2 sections4-8 target100perclass and executeeverypossible stage','rights':'Existing Gateway MIT and Mendeley CC BY4 verified; defanged public messages only','fields':list(packet[0]) if packet else [],'no_detector_outputs':True})
    print('Additional source candidates',len(selected),flush=True)

def review(offline=False):
    packet=read(DATA/'source/additional_outbound_packet.json')
    validate_packet(packet,csv_rows(DATA/'source/additional_candidates.csv'))
    client=Client(offline)
    aa={r['id']:r for r in batches(client,'source_review','A',packet)}
    bb={r['id']:r for r in batches(client,'source_review','B',packet)}
    disputes=[r|{'review_A':aa[r['id']],'review_B':bb[r['id']]} for r in packet if r['id'] in aa and r['id'] in bb and not source_consensus(aa[r['id']],bb[r['id']]) and (approved_source(aa[r['id']]) or approved_source(bb[r['id']]))]
    jj={r['id']:r for r in batches(client,'source_review','J',disputes)}
    decisions=[]
    for r in packet:
        ident=r['id'];a,b,j=aa.get(ident),bb.get(ident),jj.get(ident)
        consensus=bool(a and b and source_consensus(a,b));annotation=a if consensus else j
        ok=bool(a and b and approved_source(annotation) and (consensus or j))
        decisions.append({'frame_id':ident,'approved':ok,'A':a,'B':b,'J':j,'annotation':annotation if ok else None})
    immutable_json(DATA/'review/additional_source_decisions.json',decisions)
    print('Additional approvals',sum(r['approved'] for r in decisions),flush=True)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('stage',choices=['prepare','review']);p.add_argument('--offline',action='store_true');a=p.parse_args();prepare() if a.stage=='prepare' else review(a.offline)
