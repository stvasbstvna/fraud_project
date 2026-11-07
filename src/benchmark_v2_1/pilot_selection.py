"""Select source-review candidates, not approved truth, with template and contamination controls."""
from __future__ import annotations
import json
import hashlib
from collections import Counter
import pandas as pd
from .core import ROOT,DATA,RESULTS,defang,write_csv,write_json
from .pilot_templates import VERSION,assign_families,template_text,nearest,pair_similarity
from .pilot_sources import entity_hint,category


def select_candidates(frame,per_label=24):
    data=frame[frame.selection_eligible.astype(str).str.lower().eq('true')].copy()
    selected=[];families=set();source_counts=Counter();category_counts=Counter();entity_counts=Counter()
    for _ in range(per_label):
        for label in ['phishing_scam','legitimate']:
            options=[r for r in data.to_dict('records') if r['candidate_label']==label
                and r['template_family_id'] not in families and source_counts[r['source_id']]<per_label
                and entity_counts[str(r.get('entity','')).casefold()]<4
                and category_counts[(label,r.get('intent_category','unknown'))]<4]
            if not options:continue
            r=min(options,key=lambda r:(category_counts[(label,r.get('intent_category','unknown'))],
                source_counts[r['source_id']],entity_counts[str(r.get('entity','')).casefold()],r['frame_id']))
            selected.append(r);families.add(r['template_family_id']);source_counts[r['source_id']]+=1
            category_counts[(label,r.get('intent_category','unknown'))]+=1;entity_counts[str(r.get('entity','')).casefold()]+=1
    return pd.DataFrame(selected,columns=frame.columns)


def main():
    external=pd.read_csv(DATA/'source/pilot_external_audit_rows.csv',keep_default_na=False)
    master=pd.read_csv(DATA/'source/frames.csv',keep_default_na=False)
    # Old candidate labels never become approved. Synthetic phishing intent was
    # explicitly unestablished; do not recycle it to fill this pilot's positives.
    legacy=[]
    for r in master.to_dict('records'):
        legacy.append({**r,'candidate_label':r['true_label'],'true_label':'',
            'aggregator':'internal','original_dataset':r['source_dataset'],'original_url':'internal',
            'label_source':'legacy synthetic planning label; no independent semantic review','raw_label':r['true_label'],
            'safe_text':r['defanged_text'],'source_validated':'pending','label_validated':'pending',
            'selection_eligible':r['true_label']=='legitimate','intent_category':category(r['defanged_text']),
            'exclusion_reason':'legacy_phishing_intent_not_established' if r['true_label']!='legitimate' else '',
            'intent':'','requested_action':'','review_status':'pending'})
    pool=pd.concat([external,pd.DataFrame(legacy)],ignore_index=True).fillna('')
    reference=[]
    for path in [ROOT/'data/final/train_sms.csv',ROOT/'data/final/validation_sms.csv']:
        f=pd.read_csv(path,keep_default_na=False)
        for r in f.to_dict('records'):
            try:text=defang(r['text'])
            except ValueError:text=r['text']
            reference.append({'frame_id':r['id'],'normalized':template_text(text,entity_hint(text))})
    # Deduplicate training comparators after normalization without losing a stable witness.
    refs={}
    for r in sorted(reference,key=lambda r:r['frame_id']):refs.setdefault(r['normalized'],r)
    reference=list(refs.values())
    contamination=[]
    for i,r in pool.iterrows():
        if str(r.selection_eligible).lower()!='true':continue
        fid,score,same=nearest(r.defanged_text,r.entity,reference)
        contamination.append({'frame_id':r.frame_id,'nearest_training_or_validation_id':fid,'similarity':score,
            'template_overlap':same,'decision':'exclude' if same else 'candidate_manual_overlap_review_pending'})
        if same:
            pool.at[i,'selection_eligible']=False;pool.at[i,'exclusion_reason']='train_or_validation_template_overlap'
    clustered=assign_families(pool)
    selected=select_candidates(clustered)
    selected_ids=set(selected.frame_id);selected['pilot_complete_case']=False
    diagnostics=[];records=clustered.to_dict('records')
    # Global family IDs are assigned without labels. Nearest-neighbor witnesses
    # are computed within each family, or across selected frames for singletons.
    groups={key:g.to_dict('records') for key,g in clustered.groupby('template_family_id')}
    for r in records:
        group=[x for x in groups[r['template_family_id']] if x['frame_id']!=r['frame_id']]
        neighbors=group or [x for x in selected.to_dict('records') if x['frame_id']!=r['frame_id']]
        references=[{'frame_id':x['frame_id'],'normalized':template_text(x['defanged_text'],x.get('entity',''))} for x in neighbors]
        fid,score,_=nearest(r['defanged_text'],r.get('entity',''),references)
        diagnostics.append({'frame_id':r['frame_id'],'template_family_id':r['template_family_id'],
            'similarity_basis':VERSION+': placeholders/entities/numbers normalized; token Jaccard and SequenceMatcher; connected components',
            'nearest_frame_id':fid,'similarity':score,'decision':'selected_candidate' if r['frame_id'] in selected_ids else 'not_selected',
            'notes':r.get('exclusion_reason','')})
    write_csv(DATA/'source/pilot_48_candidates.csv',selected.to_dict('records'),list(selected.columns))
    write_csv(DATA/'source/pilot_audited_candidate_pool.csv',clustered.to_dict('records'),list(clustered.columns))
    write_csv(RESULTS/'diagnostics/pilot_template_families.csv',diagnostics,list(diagnostics[0]))
    write_csv(RESULTS/'diagnostics/pilot_training_overlap.csv',contamination,list(contamination[0]))
    # Selected pairs must pass both one-family and direct near-duplicate checks.
    for i,a in enumerate(selected.to_dict('records')):
        for b in selected.to_dict('records')[i+1:]:
            if pair_similarity(template_text(a['defanged_text'],a['entity']),template_text(b['defanged_text'],b['entity']))[2]:
                raise RuntimeError('Selected near-duplicate pair')
    write_json(RESULTS/'diagnostics/pilot_selection_summary.json',{'status':'PILOT NOT READY',
        'input_hashes':{p.relative_to(ROOT).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in [
            DATA/'source/pilot_external_audit_rows.csv',DATA/'source/frames.csv',ROOT/'data/final/train_sms.csv',ROOT/'data/final/validation_sms.csv']},
        'template_version':VERSION,
        'legacy_master_candidates':len(master),'external_financial_audit_rows':len(external),'audited_pool':len(pool),
        'master_template_families':int(clustered[clustered.source_id.eq('SYNTH-V21')].template_family_id.nunique()),
        'pool_template_families':int(clustered.template_family_id.nunique()),
        'training_template_overlap_exclusions':sum(r['template_overlap'] for r in contamination),
        'selected_frames':len(selected),'candidate_labels':selected.candidate_label.value_counts().to_dict(),
        'selected_sources':selected.source_id.value_counts().to_dict(),'selected_entities':selected.entity.value_counts().to_dict(),
        'observed_max_source_share':float(selected.source_id.value_counts().max()/len(selected)) if len(selected) else None,
        'current_cohort_source_balanced':bool(len(selected)>0 and selected.source_id.value_counts().max()<=len(selected)/2),
        'blocking_quality_flags':['target control count not reached','source/label imbalance in reduced candidate cohort','independent source review missing'],
        'selected_intent_categories':selected.intent_category.value_counts().to_dict(),
        'selected_template_families':int(selected.template_family_id.nunique()),'selected_near_duplicate_pairs':0,
        'source_approved_frames':0,'generated_rewrites':0,'frozen_rows':0,
        'targets':{'phishing_scam':24,'legitimate':24},'quota_deficit':{label:max(0,24-int(selected.candidate_label.eq(label).sum())) for label in ['phishing_scam','legitimate']},
        'selection_policy':'deterministic category/source/entity balancing; one per connected family; max 4/entity and label/category; max 24/source; no quotas filled from HOLD or train-template-overlap rows',
        'template_thresholds':{'jaccard_and_structure':.8,'structure_with_jaccard_at_least_0_45':.92},
        'limitations':['Automated family screening is not human equivalence review','Family IDs are cohort/version dependent',
            'Candidate labels are unvalidated','Source/label composition may remain confounded, particularly synthetic controls']})
    print(json.dumps({'selected_candidates':len(selected),'candidate_labels':selected.candidate_label.value_counts().to_dict(),
        'distinct_families':int(selected.template_family_id.nunique()),'source_approvals':0}))


if __name__=='__main__':main()
