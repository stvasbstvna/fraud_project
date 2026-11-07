"""Preserved-run correction for a post-score discovered template leak.

No original research artifact is overwritten. Model hyperparameters are fixed.
"""
import argparse
from collections import Counter
import json
import re
import pandas as pd
from . import core
from .core import DATA,RESULTS,MODELS,CONFIG,read_json,save_json,save_csv,save_bytes,digest,file_digest
from . import cohort as grouping
from .semantic_review import Client,payload,acceptable,decide

CD=DATA/'corrected_run';CR=RESULTS/'corrected_run';CM=MODELS/'corrected_run'
BASE_STRUCTURAL=grouping.structural_text


def corrected_structural_text(text):
    # Conservative source-only family widening, not a source-text rewrite.
    if re.search(r'you have registered\s+.+?\s+as payee',text,re.I):
        text=re.sub(r'(?i)\bURN\b\s*(?:<#>|\[[^]]+\])?\s*','URN ',text)
        text=re.sub(r'(?is)(beware of frauds\.).*',r'\1',text)
    return BASE_STRUCTURAL(text)


def prepare():
    candidates=pd.read_csv(DATA/'candidates/permitted_financial_candidates.csv',keep_default_na=False,low_memory=False)
    lookup={r['id']:r for r in candidates.to_dict('records')}
    check_ids=['mendeley-4','nus-5489']
    items=[payload(lookup[i])|{'policy_query':'Apply the EXISTING exclusion of personal coordination: is this actually a financial-service transaction/security/verification notice, or personal account/payment coordination? Do not assume that a bank/payment word makes it a legitimate financial control. Source-only reassessment; no model outcomes are supplied.'} for i in check_ids]
    client=Client(version='v3.1');a=client.call('A',{'items':items});b=client.call('B',{'items':items})
    aa={r['id']:r for r in a['output']['items']};bb={r['id']:r for r in b['output']['items']}
    disputed=[r for r in items if not decide(aa[r['id']],bb[r['id']],version='v3.1')['approved'] and (acceptable(aa[r['id']],'v3.1') or acceptable(bb[r['id']],'v3.1'))]
    j=client.call('J',{'items':[r|{'review_A':aa[r['id']],'review_B':bb[r['id']]} for r in disputed]}) if disputed else None
    jj={r['id']:r for r in j['output']['items']} if j else {}
    policy={i:decide(aa[i],bb[i],jj.get(i),version='v3.1') for i in check_ids}
    save_json(CD/'provenance/source_policy_check.json',{'A_hash':a['request_hash'],'B_hash':b['request_hash'],'J_hash':j['request_hash'] if j else '', 'decisions':policy,'selection_basis':'independent source-policy audit, not detector error analysis'})
    plan={'version':'v3.2-corrected-run','original_run_status':'INVALIDATED_FOR_CROSS_TEMPLATE_LEAKAGE',
          'confirmed_pair':['mendeley-334','mendeley-1361'],'correction':'Conservatively unite payee-registration templates across names, optionalURNslot and security suffix.',
          'policy_checks':check_ids,'model_hyperparameters':'UNCHANGED','old_files_overwritten':False,
          'evaluation_status':'all corrected results exploratory; already-inspected source pool is not a fresh confirmatory sample',
          'robustness':'Reuse only unchanged approved stimuli whose frame IDs remain in corrected heldout; selection uses IDs/family membership only; rescore corrected models, never reuse original probabilities.'}
    save_json(CONFIG/'template_correction_v3_2.json',plan)
    save_json(RESULTS/'diagnostics/post_score_template_leakage.json',plan)
    approved=[];attrition=[]
    for stage in ['controls','positives']:
        for d in pd.read_csv(DATA/f'review/{stage}_v3_1_decisions.csv',keep_default_na=False).to_dict('records'):
            row=lookup[d['id']];decision=grouping.verify_review(row,d)
            if row['id'] in policy:decision=policy[row['id']]
            ok=decision['approved'] and not grouping.policy_veto(row['safe_text'])
            attrition.append({'id':row['id'],'included_before_family':ok,'policy_rechecked':row['id'] in policy})
            if not ok:continue
            annotation=decision['annotation']
            approved.append(row|{'label':annotation['label'],'message_function':annotation['message_function'],
               'origin_type':'uncertain' if row['origin_type']=='uncertain' else 'real','review_type':'automated_semantic_review_not_human',
               'review_A_hash':d['review_A_hash'],'review_B_hash':d['review_B_hash'],'adjudication_hash':d['adjudication_hash']})
    grouping.structural_text=corrected_structural_text
    kept,ledger,edges=grouping.families(approved)
    cohort=grouping.stratified_partition(kept)
    source_pool=[r for r in kept if 'gateway' not in json.loads(r['family_source_origins_json'])]
    source_cohort=[dict(r,split='validation' if r['split']=='validation' else 'train') for r in grouping.stratified_partition(source_pool)]
    source_cohort += [dict(r,split='source_test') for r in kept if 'gateway' in json.loads(r['family_source_origins_json'])]
    if core.leakage_errors(cohort) or core.leakage_errors(source_cohort):raise ValueError('Corrected split leakage')
    for x in [cohort,source_cohort]:
        pair=[r for r in x if r['id'] in ['mendeley-334','mendeley-1361']]
        if len(pair)>1:raise ValueError('Payee duplicate representatives survived')
    save_csv(CD/'frozen/modeling_cohort.csv',cohort);save_csv(CD/'frozen/source_holdout_cohort.csv',source_cohort)
    save_bytes(CD/'provenance/source_registry.csv',(DATA/'provenance/source_registry.csv').read_bytes())
    save_json(CR/'acquisition_summary.json',read_json(RESULTS/'acquisition_summary.json'))
    save_csv(CR/'diagnostics/template_families.csv',ledger);save_csv(CR/'diagnostics/template_edges.csv',edges)
    save_csv(CR/'diagnostics/semantic_attrition.csv',attrition)
    manifest=read_json(DATA/'frozen/cohort_manifest.json')
    manifest.update(status='FROZEN_CORRECTED_EXPLORATORY_CONTROL_TARGET_NOT_MET',rows=len(cohort),labels=dict(Counter(r['label'] for r in cohort)),
        sources=dict(Counter(r['source_id'] for r in cohort)),origin_types=dict(Counter(r['origin_type'] for r in cohort)),template_families=len(cohort),
        cohort_sha256=file_digest(CD/'frozen/modeling_cohort.csv'),source_holdout_cohort_sha256=file_digest(CD/'frozen/source_holdout_cohort.csv'),
        primary_split_counts={s:dict(Counter(r['label'] for r in cohort if r['split']==s)) for s in ['train','validation','held_out_test']},
        source_holdout_counts=dict(Counter(r['split'] for r in source_cohort)),source_holdout_label_counts=dict(Counter(r['label'] for r in source_cohort if r['split']=='source_test')),
        raw_machine_approved=len(approved),template_exclusions=len(approved)-len(kept),
        correction_plan_sha256=file_digest(CONFIG/'template_correction_v3_2.json'),previous_cohort_sha256=read_json(DATA/'frozen/cohort_manifest.json')['cohort_sha256'])
    save_json(CD/'frozen/cohort_manifest.json',manifest)
    save_json(CR/'diagnostics/leakage_audit.json',{'status':'CORRECTED_SPLIT_VERIFIED_BEFORE_REFIT','exact_cross_split':False,'template_cross_split':False,'source_holdout_origin_cross_split':False,
       'known_payee_template_united':True,'original_run_invalidated':True,'correction_policy':'conservative family merge; no thresholds/hyperparameters tuned on performance',
       'labels':'machine-reviewed, not independent human annotation'})
    # No generation repeats: retain only fixed stimuli still held out after correction.
    raw=read_json(DATA/'robustness/frozen_approved_variants.json');ids={r['id'] for r in cohort if r['split']=='held_out_test'}
    stimuli=[r for r in raw if r['frame_id'] in ids]
    from .robustness import complete_core
    fm=read_json(DATA/'robustness/freeze_manifest.json')
    fm.update(status='FROZEN_CORRECTED_HELDOUT_INTERSECTION',source_frames=sum(r['condition']=='C0' for r in stimuli),
       source_labels=dict(Counter(r['label'] for r in stimuli if r['condition']=='C0')),accepted_rewrites=sum(r['condition']!='C0' for r in stimuli),
       condition_counts=dict(Counter(r['condition'] for r in stimuli)),complete_core_frames=complete_core(stimuli),
       complete_core_labels=dict(Counter(r['label'] for r in stimuli if r['condition']=='C0' and r['frame_id'] in complete_core(stimuli))),
       correction_note='Immutable original stimuli filtered by corrected heldout ID intersection; generation remains blind; no new generation or result-driven text edits')
    save_json(CD/'robustness/frozen_approved_variants.json',stimuli);fm['frozen_sha256']=file_digest(CD/'robustness/frozen_approved_variants.json')
    save_json(CD/'robustness/freeze_manifest.json',fm)
    print(json.dumps(manifest,indent=2));print('CorrectedC',fm['source_frames'],fm['accepted_rewrites'])


def activate(include_reports=False):
    from . import protocol,baselines,evaluation,statistics
    protocol.DATA=CD
    modules=[baselines,evaluation,statistics]
    if include_reports:
        from . import reports
        modules.append(reports)
    for module in modules:
        if hasattr(module,'DATA'):module.DATA=CD
        if hasattr(module,'RESULTS'):module.RESULTS=CR
        if hasattr(module,'MODELS'):module.MODELS=CM


def main():
    p=argparse.ArgumentParser();p.add_argument('stage',choices=['prepare','lexical','modern_train','modern_infer','evaluate','statistics','reports','C_infer','C_evaluate']);a=p.parse_args()
    if a.stage=='prepare':return prepare()
    prepared=None
    if a.stage.startswith('C_'):
        from . import robustness_evaluation as supplement
        original_rows,_=supplement.verify_supplement()
        frozen_rows=read_json(CD/'robustness/frozen_approved_variants.json');frozen_manifest=read_json(CD/'robustness/freeze_manifest.json')
        core.verify_hash(CD/'robustness/frozen_approved_variants.json',frozen_manifest['frozen_sha256'])
        allowed={r['id']:r for r in pd.read_csv(CD/'frozen/modeling_cohort.csv',keep_default_na=False).to_dict('records') if r['split']=='held_out_test'}
        expected=[r for r in original_rows if r['frame_id'] in allowed]
        if frozen_rows!=expected or any(r['source_text_sha256']!=digest(allowed[r['frame_id']]['safe_text']) for r in frozen_rows):raise ValueError('Corrected supplement is not exact current-heldout intersection')
        prepared=(frozen_rows,frozen_manifest)
    activate(include_reports=a.stage=='reports')
    if a.stage=='lexical':
        from .baselines import train
        train('primary');train('source_holdout')
    elif a.stage=='modern_train':
        from .modernbert import train
        for experiment,name,out in [('primary','modeling_cohort.csv','modernbert'),('source_holdout','source_holdout_cohort.csv','modernbert_source_holdout')]:
            config=read_json(CONFIG/'modernbert_training.json')|{'experiment_status':'CORRECTED_EXPLORATORY_SMALL_CONTROL_COHORT'}
            train(CD/'frozen'/name,CM/out,config)
    elif a.stage=='modern_infer':
        from .evaluation import modern_cache
        modern_cache('primary');modern_cache('source_holdout')
    elif a.stage=='evaluate':
        from .evaluation import evaluate
        evaluate('primary',True);evaluate('source_holdout',True)
    elif a.stage=='statistics':
        from .statistics import main
        main()
    elif a.stage=='reports':
        from .reports import main
        main()
    elif a.stage.startswith('C_'):
        supplement.MODELS=CM;supplement.RESULTS=CR
        supplement.modern_cache(prepared) if a.stage=='C_infer' else supplement.evaluate(prepared)


if __name__=='__main__':main()
