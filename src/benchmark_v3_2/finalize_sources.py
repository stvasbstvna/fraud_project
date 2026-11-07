"""Preserve preliminary approvals, apply source-only eligibility findings, freeze final C0."""
from .core import *
from .sources import validate_packet

EXCLUDE={
    'nus-3592':'UniPay2U gold monthly bonus investment claim: institutional legitimacy unresolved; no confident legitimate control',
    'nus-1889':'Developer-company bank details sharing, not institutional financial-service notification',
    'nus-3847':'Unspecified refill/pay-retailer service, possible telco top-up; financial eligibility unresolved',
    'gateway-8251':'Generic account identity verification with no explicit financial institution or financial event'
}

def finalize():
    if (DATA/'frozen/final_source_stage.json').exists():return read(DATA/'frozen/final_source_stage.json')
    first=csv_rows(DATA/'source/review_candidates.csv');additional=csv_rows(DATA/'source/additional_candidates.csv')
    packet=read(DATA/'source/outbound_packet.json')+read(DATA/'source/additional_outbound_packet.json')
    lookup=validate_packet(packet,first+additional)
    decisions=read(DATA/'review/recovered_combined_source_decisions.json') if (DATA/'review/recovered_combined_source_decisions.json').exists() else read(DATA/'review/source_decisions.json')+read(DATA/'review/additional_source_decisions.json')
    selected=[];exclusions=[]
    for d in decisions:
        if not d['approved']:continue
        ident=d['frame_id'];a=d['annotation'];r=lookup[ident]
        if ident in EXCLUDE:
            exclusions.append({'frame_id':ident,'semantic_review_label':a['label'],'decision':'exclude_not_relabel','reason':EXCLUDE[ident],'before_generation_and_scoring':True});continue
        origin=r.get('origin_type','uncertain')
        origin='real_source' if origin in {'real','real_source','real_source_candidate'} else 'synthetic' if origin=='synthetic' else 'uncertain_origin'
        selected.append({'frame_id':ident,'id':ident,'safe_text':r['safe_text'],'source_dataset':r['source_id'],'source_row_id':r['source_row_id'],'original_url':r.get('source_url',''),'original_label':r.get('raw_label',''),'validated_label':a['label'],'true_label':int(a['label']=='phishing'),'origin_type':origin,'license_status':r.get('license_status') or {'mendeley':'CC_BY_4_0','uci':'CC_BY_4_0','nus':'AUTHOR_UNLIMITED_USE','gateway':'MIT_DATA_RELEASE'}.get(r['source_id'],'NOT_VERIFIED'),'template_family_id':r['template_family_id'],**{k:a[k] for k in ['intent','requested_action','institution_entity','destination','message_function','event_or_claim','language','channel']},'destination_type':a['destination'],'source_text_sha256':sha(r['safe_text']),'C2_eligible':False,'C2_ineligibility_reason':'Optional_secondary_not_selected','C3_eligible':False,'C3_ineligibility_reason':'Optional_secondary_not_selected'})
    final=[]
    for label in [0,1]:final.extend(sorted([r for r in selected if r['true_label']==label and r['origin_type']!='synthetic'],key=lambda r:sha('42:'+r['frame_id']))[:100])
    if not final:raise ValueError('No valid cohort')
    # No generation or scoring has begun: preserve preliminary freeze explicitly.
    if (DATA/'generated/initial_jobs.json').exists():raise ValueError('Cannot revise C0 after generation')
    archive=DATA/'source/history/pre_policy_initial_freeze';archive.mkdir(parents=True,exist_ok=True)
    for name in ['source_cohort.csv','source_manifest.json']:
        path=DATA/'frozen'/name
        if path.exists():path.rename(archive/name)
    write_csv(DATA/'source/source_eligibility_exclusions.csv',exclusions)
    immutable_json(DATA/'review/final_source_decisions.json',decisions)
    write_csv(DATA/'frozen/source_cohort.csv',final)
    manifest={'frozen_at':now(),'source_cohort_sha256':file_sha(DATA/'frozen/source_cohort.csv'),'source_decisions_sha256':file_sha(DATA/'review/final_source_decisions.json'),'rows':len(final),'labels':dict(Counter(r['validated_label'] for r in final)),'origins':dict(Counter(r['origin_type'] for r in final)),'families':len({r['template_family_id'] for r in final}),'source_review_packets':[{'path':str(p.relative_to(ROOT)),'sha256':file_sha(p)} for p in [DATA/'source/outbound_packet.json',DATA/'source/additional_outbound_packet.json']],'eligibility_exclusions':exclusions,'status':'FINAL_C0_EXPLORATORY_CONTROL_TARGET_UNMET','review_type':'automated contexts; independent code/source audit not independent human ground truth'}
    immutable_json(DATA/'frozen/source_manifest.json',manifest)
    immutable_json(DATA/'frozen/final_source_stage.json',manifest)
    immutable_text(DOCS/'CORRECTION_20261107_PRE_GENERATION_ELIGIBILITY.md','# Source-only eligibility correction before generation\n\nThe preliminary source freeze contained12 automatic approvals (8phishing/4legitimate). Independent source-content audit found four policy-ineligible/ambiguous records, excluded without relabeling. Initial freeze and original reviewer decisions are preserved. A separately reviewed additional23-source packet expands potential phishing family capacity. These changes precede every v3.2 generation and detector score; prompts, review model snapshots, statistical plan and detector models remain unchanged. Final counts and exact exclusion reasons are in frozen/source_manifest.json and source/source_eligibility_exclusions.csv. No prior v3 result changes.\n\nUniPay2U concerns do not prove this SMS phishing: uncertainty defeats confident legitimate inclusion. Relevant original institutional evidence: https://icmab.gov.bd/wp-content/uploads/2019/12/Journal-September-October-2016.pdf (p25) and https://www.bssnews.net/news/177100.\n')
    print(json.dumps(manifest,indent=2),flush=True)
    return manifest
if __name__=='__main__':finalize()
