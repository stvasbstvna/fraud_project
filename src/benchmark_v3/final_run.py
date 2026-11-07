"""Final source-eligibility correction; all earlier scored runs stay preserved."""
import argparse
from collections import Counter
import json
import pandas as pd
from . import correction
from .core import DATA,RESULTS,MODELS,CONFIG,read_json,save_json,save_csv,save_bytes,file_digest,digest,leakage_errors
from .cohort import stratified_partition

FD=DATA/'final_run';FR=RESULTS/'final_run';FM=MODELS/'final_run'


def verify_eligibility():
    from .robustness_evaluation import call
    from .final_eligibility import decide
    decisions=read_json(DATA/'final_eligibility_audit/final_decisions.json')
    previous=pd.read_csv(DATA/'corrected_run/frozen/modeling_cohort.csv',keep_default_na=False)
    lookup={r['id']:r for r in previous.to_dict('records')}
    if {r['id'] for r in decisions}!=set(lookup) or len(decisions)!=len(lookup):raise ValueError('Incomplete final eligibility coverage')
    for d in decisions:
        row=lookup[d['id']]
        if d['safe_text']!=row['safe_text'] or d['label']!=row['label'] or d['source_text_sha256']!=digest(row['safe_text']):raise ValueError('Final audit source binding mismatch')
        for role in ['A','B','J']:
            annotation=d.get(role)
            if not annotation:continue
            inputs,outputs=call(role,annotation['review_request_sha256'],DATA/'final_eligibility_audit')
            supplied=inputs[row['id']]
            if any(supplied[k]!=row[k] for k in ['id','safe_text','label','source_id']):raise ValueError('Final audit request source mismatch')
            if outputs[row['id']]!={k:v for k,v in annotation.items() if k!='review_request_sha256'}:raise ValueError('Final audit response mismatch')
            if role=='J' and (supplied.get('A')!=d['A'] or supplied.get('B')!=d['B']):raise ValueError('Final audit adjudication chain mismatch')
        if decide(d.get('A'),d.get('B'),d.get('J'),row['label'])['retained']!=d['retained']:raise ValueError('Final eligibility decision cannot reproduce')
    return decisions


def prepare():
    decisions=verify_eligibility()
    if isinstance(decisions,dict):decisions=decisions['decisions']
    keep={r['id'] for r in decisions if r['retained']}
    previous=pd.read_csv(DATA/'corrected_run/frozen/modeling_cohort.csv',keep_default_na=False)
    if set(r['id'] for r in decisions)!=set(previous.id):raise ValueError('Final eligibility audit must bind every previous representative')
    rows=[r for r in previous.to_dict('records') if r['id'] in keep]
    cohort=stratified_partition(rows)
    fitting=[r for r in rows if 'gateway' not in json.loads(r['family_source_origins_json'])]
    source=[dict(r,split='validation' if r['split']=='validation' else 'train') for r in stratified_partition(fitting)]
    source += [dict(r,split='source_test') for r in rows if 'gateway' in json.loads(r['family_source_origins_json'])]
    if leakage_errors(cohort) or leakage_errors(source):raise ValueError('Final cohort split leakage')
    save_csv(FD/'frozen/modeling_cohort.csv',cohort);save_csv(FD/'frozen/source_holdout_cohort.csv',source)
    save_bytes(FD/'provenance/source_registry.csv',(DATA/'provenance/source_registry.csv').read_bytes())
    save_json(FR/'acquisition_summary.json',read_json(RESULTS/'acquisition_summary.json'))
    prior=read_json(DATA/'corrected_run/frozen/cohort_manifest.json')
    prior.update(status='FROZEN_FINAL_EXPLORATORY_SOURCE_QA_CORRECTED',rows=len(rows),labels=dict(Counter(r['label'] for r in rows)),
        sources=dict(Counter(r['source_id'] for r in rows)),origin_types=dict(Counter(r['origin_type'] for r in rows)),template_families=len(rows),
        primary_split_counts={s:dict(Counter(r['label'] for r in cohort if r['split']==s)) for s in ['train','validation','held_out_test']},
        source_holdout_counts=dict(Counter(r['split'] for r in source)),source_holdout_label_counts=dict(Counter(r['label'] for r in source if r['split']=='source_test')),
        cohort_sha256=file_digest(FD/'frozen/modeling_cohort.csv'),source_holdout_cohort_sha256=file_digest(FD/'frozen/source_holdout_cohort.csv'),
        previous_cohort_sha256=read_json(DATA/'corrected_run/frozen/cohort_manifest.json')['cohort_sha256'],
        final_eligibility_plan_sha256=file_digest(CONFIG/'final_eligibility_plan.json'),final_eligibility_decisions_sha256=file_digest(DATA/'final_eligibility_audit/final_decisions.json'),
        final_eligibility_exclusions=len(previous)-len(rows),
        correction_note='Explicit full-cohort language/financial eligibility audit corrects ASCII false positives before final refits. Labels are not flipped; retained cases keep their prior labels. Hyperparameters unchanged; earlier inspected pools mean exploratory results only.')
    save_json(FD/'frozen/cohort_manifest.json',prior)
    # Reuse unchanged blind stimuli only where source remains in FINAL heldout.
    raw=read_json(DATA/'robustness/frozen_approved_variants.json');held={r['id'] for r in cohort if r['split']=='held_out_test'}
    stimuli=[r for r in raw if r['frame_id'] in held]
    from .robustness import complete_core
    manifest=read_json(DATA/'robustness/freeze_manifest.json');complete=complete_core(stimuli)
    manifest.update(status='FROZEN_FINAL_ELIGIBILITY_HELDOUT_INTERSECTION',source_frames=sum(r['condition']=='C0' for r in stimuli),
       source_labels=dict(Counter(r['label'] for r in stimuli if r['condition']=='C0')),accepted_rewrites=sum(r['condition']!='C0' for r in stimuli),
       condition_counts=dict(Counter(r['condition'] for r in stimuli)),complete_core_frames=complete,
       complete_core_labels=dict(Counter(r['label'] for r in stimuli if r['condition']=='C0' and r['frame_id'] in complete)),
       correction_note='Original blind stimuli intersected with final source-eligibility heldout IDs; no regenerated text or outcome-based source selection.')
    save_json(FD/'robustness/frozen_approved_variants.json',stimuli);manifest['frozen_sha256']=file_digest(FD/'robustness/frozen_approved_variants.json')
    save_json(FD/'robustness/freeze_manifest.json',manifest)
    for name in ['template_families.csv','template_edges.csv','semantic_attrition.csv']:
        path=RESULTS/'corrected_run/diagnostics'/name
        save_bytes(FR/'diagnostics'/('prior_'+name),path.read_bytes())
    save_json(FR/'diagnostics/leakage_audit.json',{'status':'FINAL_SPLIT_VERIFIED_BEFORE_REFIT','known_payee_template_united':True,
        'exact_cross_split':False,'template_cross_split':False,'source_holdout_origin_cross_split':False,
        'all228_prior_representatives_received_explicit_eligibility_audit':True,'previous_runs_preserved_not_authoritative':True,
        'labels':'automated, not independent human annotation'})
    print(json.dumps(prior,indent=2));print('FinalC',manifest['source_frames'],manifest['accepted_rewrites'])


def activate(include_reports=False):
    correction.CD=FD;correction.CR=FR;correction.CM=FM;correction.activate(include_reports)


def main():
    p=argparse.ArgumentParser();p.add_argument('stage',choices=['prepare','lexical','modern_train','modern_infer','evaluate','statistics','reports','C_infer','C_evaluate']);a=p.parse_args()
    if a.stage=='prepare':return prepare()
    # Reuse the same path-explicit execution implementation in a fresh process.
    correction.CD=FD;correction.CR=FR;correction.CM=FM
    correction.main()


if __name__=='__main__':main()
