"""One prespecified quality retry, separate semantic review, immutable approved matrix."""
import argparse
from src.benchmark_v3.robustness import invariant_errors
from .core import *
from .calls import Client,batches

def deterministic_errors(job,answer):
    if answer is None:return ['missing_provider_evidence']
    errors=invariant_errors(job['source'],answer['text'],job['condition'],job['semantic_controls']['institution_entity'])
    legacy=lambda s:Counter(re.findall(r'<(?:#|[A-Z][A-Z0-9_-]*)>',s))
    if legacy(job['source'])!=legacy(answer['text']) and 'placeholders' not in errors:errors.append('placeholders')
    return errors

def verify_prefreeze():
    freeze=read(CONFIG/'pre_scoring_freeze.json')
    for path,key in [(CONFIG/'protocol.json','protocol_sha256'),(CONFIG/'generator_config.json','generator_config_sha256'),(CONFIG/'PROMPT_REGISTRY.csv','prompt_registry_sha256'),(DOCS/'STATISTICAL_ANALYSIS_PLAN.md','statistical_plan_sha256')]:
        if file_sha(path)!=freeze[key]:raise ValueError('Prescoring plan changed')
    for model in read(MODELS/'MODEL_FREEZE_MANIFEST.json')['models']:
        if file_sha(ROOT/model['model_path'])!=model['sha256']:raise ValueError('Frozen detector changed')
    source=read(DATA/'frozen/source_manifest.json')
    if file_sha(DATA/'frozen/source_cohort.csv')!=source['source_cohort_sha256']:raise ValueError('Source freeze changed')
    verify_protected()

def generate(offline=False):
    verify_prefreeze()
    if (DATA/'frozen/matrix_manifest.json').exists():return read(DATA/'frozen/matrix_manifest.json')
    sources=csv_rows(DATA/'frozen/source_cohort.csv');client=Client(offline)
    jobs=[]
    for source in sources:
        controls={k:source[k] for k in ['intent','requested_action','institution_entity','destination','message_function','event_or_claim','validated_label']}
        for c in CONDITIONS[1:]:
            jobs.append({'id':source['frame_id']+'::'+c+'::0','frame_id':source['frame_id'],'condition':c,'attempt':0,'source':source['safe_text'],'semantic_controls':controls})
    immutable_json(DATA/'generated/initial_jobs.json',jobs)
    output={}
    for c in CONDITIONS[1:]:
        output.update({r['id']:r for r in batches(client,'generation','G',[r for r in jobs if r['condition']==c],c,0,size=12)})
    errors=deterministic_errors
    retry=[]
    for j in jobs:
        errs=errors(j,output.get(j['id']))
        if retry_allowed(0,errs):retry.append(j|{'id':j['frame_id']+'::'+j['condition']+'::1','attempt':1,'quality_failure_reasons':errs})
    immutable_json(DATA/'generated/retry_jobs.json',retry)
    for c in CONDITIONS[1:]:
        output.update({r['id']:r for r in batches(client,'generation','G',[r for r in retry if r['condition']==c],c,1,size=12)})
    alljobs=jobs+retry
    # Every actually generated variant is submitted to both semantic reviewers,
    # including deterministic failures; those failures can never be overridden.
    reviewjobs=[{**j,'text':output[j['id']]['text']} for j in alljobs if j['id'] in output]
    aa={r['id']:r for r in batches(client,'rewrite_review','A',reviewjobs,size=12)}
    bb={r['id']:r for r in batches(client,'rewrite_review','B',reviewjobs,size=12)}
    disputed=[j|{'review_A':aa[j['id']],'review_B':bb[j['id']]} for j in reviewjobs if j['id'] in aa and j['id'] in bb and any(aa[j['id']][k]!=bb[j['id']][k] for k in GATES)]
    jj={r['id']:r for r in batches(client,'rewrite_review','J',disputed,size=12)}
    decisions=[];attempts=[];accepted={}
    for j in alljobs:
        ident=j['id'];answer=output.get(ident);errs=errors(j,answer)
        a,b,q=aa.get(ident),bb.get(ident),jj.get(ident)
        agree=bool(a and b and all(a[k]==b[k] for k in GATES))
        semantic=bool(a and b and ((agree and approved_rewrite(a) and approved_rewrite(b)) or (not agree and approved_rewrite(q))))
        ok=not errs and semantic
        decision={**j,'generation':answer,'deterministic_errors':errs,'A':a,'B':b,'J':q,'approved':ok}
        decisions.append(decision)
        attempts.append({'frame_id':j['frame_id'],'condition':j['condition'],'attempt':j['attempt'],'id':ident,'status':'approved' if ok else 'rejected','generated':answer is not None,'text':answer['text'] if answer else '', 'text_sha256':sha(answer['text']) if answer else '', 'generation_request_sha256':answer['evidence_request_sha256'] if answer else '', 'rejection_reasons':';'.join(errs) or ('' if ok else 'semantic_rejection_or_missing_evidence')})
        key=(j['frame_id'],j['condition'])
        if ok and key not in accepted:accepted[key]=decision
    immutable_json(DATA/'review/rewrite_decisions.json',decisions)
    write_csv(DATA/'generated/attempts.csv',attempts)
    matrix=[]
    for source in sources:
        base={k:source[k] for k in ['frame_id','true_label','validated_label','source_dataset','source_row_id','origin_type','template_family_id','source_text_sha256']}
        matrix.append(base|{'condition':'C0','text':source['safe_text'],'text_sha256':sha(source['safe_text']),'generation_request_sha256':'','attempt':''})
        for c in CONDITIONS[1:]:
            d=accepted.get((source['frame_id'],c))
            if d:
                text=d['generation']['text']
                matrix.append(base|{'condition':c,'text':text,'text_sha256':sha(text),'generation_request_sha256':d['generation']['evidence_request_sha256'],'attempt':d['attempt']})
    complete=complete_ids(matrix)
    for r in matrix:r['primary_complete_case']=r['frame_id'] in complete
    write_csv(DATA/'frozen/robustness_matrix.csv',matrix)
    manifest={'frozen_at':now(),'source_cohort_sha256':file_sha(DATA/'frozen/source_cohort.csv'),'matrix_sha256':file_sha(DATA/'frozen/robustness_matrix.csv'),'decisions_sha256':file_sha(DATA/'review/rewrite_decisions.json'),'source_frames':len(sources),'initial_jobs':len(jobs),'retry_jobs':len(retry),'generated_attempts':sum(r['generated'] for r in attempts),'approved_pairs':len(accepted),'complete_frames':len(complete),'complete_by_class':dict(Counter(s['validated_label'] for s in sources if s['frame_id'] in complete)),'approved_conditions':dict(Counter(c for f,c in accepted)),'status':'FROZEN_EXPLORATORY','statistical_plan_sha256':file_sha(DOCS/'STATISTICAL_ANALYSIS_PLAN.md'),'model_freeze_sha256':file_sha(MODELS/'MODEL_FREEZE_MANIFEST.json'),'prompt_registry_sha256':file_sha(CONFIG/'PROMPT_REGISTRY.csv')}
    immutable_json(DATA/'frozen/matrix_manifest.json',manifest)
    print(json.dumps(manifest,indent=2),flush=True)
    return manifest

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--offline',action='store_true');args=p.parse_args();generate(args.offline)
