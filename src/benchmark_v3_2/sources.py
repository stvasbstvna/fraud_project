"""Source-only cohort selection; primary-model training/validation families excluded."""
import argparse
import pandas as pd
from difflib import SequenceMatcher
from sklearn.feature_extraction.text import TfidfVectorizer
from src.benchmark_v3.correction import corrected_structural_text
from src.benchmark_v2_1.pilot_templates import pair_similarity
from .core import *
from .calls import Client,batches

def validate_packet(packet,candidates):
    lookup={r['id']:r for r in candidates}
    if len(lookup)!=len(candidates) or len({r['id'] for r in packet})!=len(packet) or set(lookup)!={r['id'] for r in packet}:raise ValueError('Source packet IDs mismatch')
    mapping={'safe_text':'safe_text','source_dataset':'source_id','source_row_id':'source_row_id','original_label':'raw_label','original_url':'source_url'}
    for r in packet:
        if r['frame_id']!=r['id'] or any(str(r[k])!=str(lookup[r['id']].get(v,'')) for k,v in mapping.items()):raise ValueError('Source packet text/provenance mismatch')
    return lookup

def family_filter(rows,reference):
    # Global conservative graph over candidate sources and protected fitting references.
    allrows=reference+rows
    if not allrows:return [],[],[]
    texts=[corrected_structural_text(r['safe_text']) for r in allrows]
    x=TfidfVectorizer(analyzer='char_wb',ngram_range=(3,5),lowercase=False).fit_transform(texts)
    similarities=(x@x.T).toarray();parent=list(range(len(allrows)));edges=[]
    def root(i):
        while parent[i]!=i:parent[i]=parent[parent[i]];i=parent[i]
        return i
    for i,a in enumerate(texts):
        for j in range(i):
            _,_,same=pair_similarity(a,texts[j])
            if not same and similarities[i,j]>=.90:same=SequenceMatcher(None,a,texts[j],autojunk=False).ratio()>=.75
            if same:
                p,q=root(i),root(j);parent[max(p,q)]=min(p,q)
                edges.append({'left_id':allrows[i]['id'],'right_id':allrows[j]['id'],'character_cosine':float(similarities[i,j])})
    groups=defaultdict(list)
    for i,r in enumerate(allrows):groups[root(i)].append((i,r))
    kept=[];ledger=[]
    for members in groups.values():
        blocked=any(i<len(reference) for i,r in members)
        candidates=[r for i,r in members if i>=len(reference)]
        fid='V32-TF-'+sha('\n'.join(sorted({texts[i] for i,r in members})))[:20]
        representative=min(candidates,key=lambda r:sha('42:'+r['id'])) if candidates else None
        for r in candidates:
            use=not blocked and r['id']==representative['id']
            ledger.append({'frame_id':r['id'],'template_family_id':fid,'family_size':len(members),'training_validation_overlap':blocked,'representative':use})
            if use:kept.append(r|{'template_family_id':fid})
    return kept,ledger,edges

def build_packet():
    verify_protected()
    old=pd.read_csv(ROOT/'data/benchmark_v3/final_run/frozen/modeling_cohort.csv',keep_default_na=False).to_dict('records')
    reference=[r for r in old if r['split']!='held_out_test']
    pool=pd.read_csv(ROOT/'data/benchmark_v3/candidates/permitted_financial_candidates.csv',keep_default_na=False,low_memory=False).to_dict('records')
    # Old source review covers all ham/uncertain controls; new metadata review still required.
    reviewed=set()
    for stage in ['controls','positives']:
        reviewed.update(r['id'] for r in csv_rows(ROOT/f'data/benchmark_v3/review/{stage}_v3_1_decisions.csv'))
    oldapproved={r['id'] for r in old}
    controls=[r for r in pool if r['source_id']!='gateway' and r['raw_label'].lower() not in {'phishing','smishing'} and 20<=len(r['safe_text'])<=1000]
    positives=[r for r in old if r['label']=='phishing']
    # A bounded source-only expansion: known reviewed sources plus every new locally acquired control candidate.
    extra=DATA/'source/new_source_candidates.csv'
    if extra.exists():
        for r in csv_rows(extra):
            if r.get('modeling_allowed','True').lower() not in {'true','1'}:continue
            controls.append(r)
    unique={r['id']:r for r in controls+positives}
    kept,ledger,edges=family_filter(list(unique.values()),reference)
    write_csv(DATA/'source/family_screen.csv',ledger)
    write_csv(DATA/'source/family_edges.csv',edges,['left_id','right_id','character_cosine'])
    # Max all controls and 100 source-only positives; preserve candidate labels as evidence only.
    kept=sorted(kept,key=lambda r:sha('42:'+r['id']))
    selected=[];positive_count=0
    for r in kept:
        ispositive=r.get('label')=='phishing' or r.get('raw_label','').casefold() in {'phishing','smishing'}
        if ispositive:
            if positive_count>=100:continue
            positive_count+=1
        selected.append(r)
    write_csv(DATA/'source/review_candidates.csv',selected,sorted({k for r in selected for k in r}))
    packet=[{'id':r['id'],'frame_id':r['id'],'safe_text':r['safe_text'],'source_dataset':r['source_id'],'source_row_id':r['source_row_id'],'original_label':r.get('raw_label',''),'original_url':r.get('source_url','')} for r in selected]
    immutable_json(DATA/'source/outbound_packet.json',packet)
    immutable_json(DATA/'provenance/outbound_authorization.json',{'user_authorization':'Explicit v3.2 source validation, sections4-9 and execute all stages; public rights-cleared defanged SMS only','rows':len(packet),'packet_sha256':file_sha(DATA/'source/outbound_packet.json'),'fields':list(packet[0]) if packet else [],'no_secrets':True,'no_detector_feedback':True,'rights_evidence':'docs/benchmark_v3/SOURCE_LICENSE_AUDIT.md plus v3.2/SOURCE_EXPANSION_AUDIT.md','roles':ROLES,'fitting_reference_rows':len(reference)})
    print('Source review packet',len(packet),'training-reference',len(reference),flush=True)

def review(offline=False):
    packet=read(DATA/'source/outbound_packet.json');client=Client(offline)
    lookup=validate_packet(packet,csv_rows(DATA/'source/review_candidates.csv'))
    aa={r['id']:r for r in batches(client,'source_review','A',packet)}
    bb={r['id']:r for r in batches(client,'source_review','B',packet)}
    disagreements=[]
    for r in packet:
        a,b=aa.get(r['id']),bb.get(r['id'])
        if a and b and not source_consensus(a,b) and (approved_source(a) or approved_source(b)):
            disagreements.append(r|{'review_A':a,'review_B':b})
    jj={r['id']:r for r in batches(client,'source_review','J',disagreements)}
    decisions=[];accepted=[]
    for r in packet:
        ident=r['id'];a,b,j=aa.get(ident),bb.get(ident),jj.get(ident)
        consensus=bool(a and b and source_consensus(a,b));annotation=a if consensus else j
        ok=bool(a and b and approved_source(annotation) and (consensus or j))
        decisions.append({'frame_id':ident,'approved':ok,'A':a,'B':b,'J':j,'annotation':annotation if ok else None})
        if ok:
            x=lookup[ident];origin=x.get('origin_type','uncertain')
            origin='real_source' if origin in {'real','real_source','real_source_candidate'} else 'synthetic' if origin=='synthetic' else 'uncertain_origin'
            accepted.append({'frame_id':ident,'id':ident,'safe_text':x['safe_text'],'source_dataset':x['source_id'],'source_row_id':x['source_row_id'],'original_url':x.get('source_url',''),'original_label':x.get('raw_label',''),'validated_label':annotation['label'],'true_label':int(annotation['label']=='phishing'),'origin_type':origin,'license_status':x.get('license_status') or {'mendeley':'CC_BY_4_0','uci':'CC_BY_4_0','nus':'AUTHOR_UNLIMITED_USE','gateway':'MIT_DATA_RELEASE'}.get(x['source_id'],'NOT_VERIFIED'),'template_family_id':x['template_family_id'],**{k:annotation[k] for k in ['intent','requested_action','institution_entity','destination','message_function','event_or_claim','language','channel']},'destination_type':annotation['destination'],'source_text_sha256':sha(x['safe_text']),'C2_eligible':False,'C2_ineligibility_reason':'Optional_secondary_not_selected','C3_eligible':False,'C3_ineligibility_reason':'Optional_secondary_not_selected'})
    immutable_json(DATA/'review/source_decisions.json',decisions)
    selected=[]
    for label in [0,1]:selected.extend(sorted([r for r in accepted if r['true_label']==label and r['origin_type']!='synthetic'],key=lambda r:sha('42:'+r['frame_id']))[:100])
    write_csv(DATA/'frozen/source_cohort.csv',selected)
    immutable_json(DATA/'frozen/source_manifest.json',{'source_cohort_sha256':file_sha(DATA/'frozen/source_cohort.csv'),'source_decisions_sha256':file_sha(DATA/'review/source_decisions.json'),'packet_sha256':file_sha(DATA/'source/outbound_packet.json'),'candidate_sha256':file_sha(DATA/'source/review_candidates.csv'),'rows':len(selected),'labels':dict(Counter(r['validated_label'] for r in selected)),'origins':dict(Counter(r['origin_type'] for r in selected)),'families':len({r['template_family_id'] for r in selected}),'approved_before_cap':len(accepted),'review_type':'automated contexts not independent human annotation','frozen_at':now()})
    print('Approved cohort',len(selected),dict(Counter(r['validated_label'] for r in selected)),flush=True)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('stage',choices=['prepare','review']);p.add_argument('--offline',action='store_true');a=p.parse_args()
    build_packet() if a.stage=='prepare' else review(a.offline)
