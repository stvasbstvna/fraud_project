"""Traceable run ledgers and research/presentation documentation from actual artifacts."""
from datetime import datetime,timezone
import subprocess
import pandas as pd
import numpy as np
from .core import *

def markdown(rows):
    if not rows:return 'No supported observations.\n'
    keys=list(rows[0]);esc=lambda v:str(v).replace('|','/').replace('\n',' ')
    return '| '+' | '.join(keys)+' |\n| '+' | '.join(['---']*len(keys))+' |\n'+'\n'.join('| '+' | '.join(esc(r.get(k,'')) for k in keys)+' |' for r in rows)+'\n'
def mtime(path):return datetime.fromtimestamp(Path(path).stat().st_mtime,timezone.utc).isoformat()
def table(path,rows,fields=None):
    write_csv(path,rows,fields)
    immutable_text(Path(path).with_suffix('.md'),markdown(csv_rows(path)))

def pre_figures():
    source=read(DATA/'frozen/source_manifest.json');matrix=read(DATA/'frozen/matrix_manifest.json')
    initial=len(read(DATA/'source/outbound_packet.json'));additional=len(read(DATA/'source/additional_outbound_packet.json'))
    flow=[{'stage':k,'count':v,'unit':u,'note':n} for k,v,u,n in [
        ('Existing raw records rescanned',67380,'raw records','NUS55835+Mendeley5971+UCI5574; no newly downloaded SMS'),
        ('New expanded lexical hits',707,'unique uncertain candidates','Not validated financial controls; all rights eligible from known sources'),
        ('Rights-cleared unique candidate pool read',12954,'candidate texts','Prior12247 plus new707; not all semantically English/financial'),
        ('Fitting-family-compatible source packet',initial+additional,'source candidates','1042 initial plus23 additional; separate from all-candidate pool'),
        ('English/financial machine approved',sum(d['approved'] for d in read(DATA/'review/final_source_decisions.json')),'source candidates','Before4source-content policy exclusions'),
        ('Policy-eligible robustness C0',source['rows'],'source frames','Frozen before generation; labels automated'),
        ('Initial generation jobs',matrix['initial_jobs'],'frame-condition slots','Four requested conditions per source'),
        ('Generated attempts',matrix['generated_attempts'],'variant attempts','Retries included, not independent sources'),
        ('Approved rewrite pairs',matrix['approved_pairs'],'paired variants','Review and deterministic gates both passed'),
        ('Complete trajectories',matrix['complete_frames'],'source frames','C0/C1/C4/C5/C6 all approved')]]
    table(RESULTS/'tables/cohort_flow.csv',flow)
    for p in sorted((RESULTS/'manipulation').glob('*.csv')):immutable_text(p.with_suffix('.md'),markdown(csv_rows(p)))

def call_log():
    rows=[];tokens=Counter();roles=Counter();statuscounts=Counter()
    for p in sorted(DATA.rglob('*.request.json')):
        # The pre-API packet archive contains no API requests.
        request=read(p)
        if 'request_payload' not in request:continue
        payload=request['request_payload'];items=json.loads(payload['input'])['items'];response_path=p.with_name(p.name.replace('.request.json','.response.json'));error_path=p.with_name(p.name.replace('.request.json','.error.json'))
        response=read(response_path) if response_path.exists() else None
        status='failed' if error_path.exists() else 'completed' if response else 'pending'
        if response:
            usage=response['raw_response'].get('usage') or {}
            tokens.update({'input_tokens':usage.get('input_tokens',0),'output_tokens':usage.get('output_tokens',0)})
        rows.append({'call_id':request['call_id'],'run_id':request['run_id'],'phase':request['phase'],'role':request['role'],'frame_id':';'.join(str(r.get('frame_id',r['id'])) for r in items),'condition':request['condition'],'attempt':request.get('technical_attempt',request['attempt']),'prompt_id':request['prompt_id'],'prompt_sha256':request['prompt_sha256'],'model':payload['model'],'model_snapshot':payload['model'],'temperature':payload['temperature'],'top_p':payload.get('top_p',''),'seed':'unsupported_not_supplied','request_sha256':request['request_sha256'],'response_sha256':response['response_sha256'] if response else '', 'parsed_status':status,'review_status':'see exact source/rewrite decisions; completion is not approval','timestamp':request['timestamp'],'request_file':p.relative_to(ROOT).as_posix(),'response_file':response_path.relative_to(ROOT).as_posix() if response else '', 'error_file':error_path.relative_to(ROOT).as_posix() if error_path.exists() else ''})
        roles[request['role']]+=1;statuscounts[status]+=1
    write_csv(RESULTS/'PROMPT_LOG.csv',rows)
    return {'calls':len(rows),'by_role':dict(roles),'call_status':dict(statuscounts),'usage':dict(tokens)}

def reports():
    pre_figures()
    source=read(DATA/'frozen/source_manifest.json');frozen=read(DATA/'frozen/matrix_manifest.json');models=read(MODELS/'MODEL_FREEZE_MANIFEST.json')
    matrix=pd.read_csv(DATA/'frozen/robustness_matrix.csv');sources=csv_rows(DATA/'frozen/source_cohort.csv')
    primary=matrix[matrix.primary_complete_case.astype(str).str.lower().isin(['true','1'])]
    complete=primary[primary.condition.eq('C0')]
    calls=call_log();pred={n:pd.read_csv(RESULTS/f'predictions/{n}_predictions.csv') for n in ['LR','RF','ModernBERT']}
    allpred=pd.concat([d.assign(model=n) for n,d in pred.items()],ignore_index=True)
    paired=allpred[allpred.condition.ne('C0')]
    extreme=paired.sort_values(['absolute_delta','frame_id','condition','model'],ascending=[False,True,True,True]).iloc[0].to_dict() if len(paired) else None
    primary_pred=allpred[allpred.primary_complete_case.astype(str).str.lower().isin(['true','1']) & allpred.condition.ne('C0')]
    movement=primary_pred.groupby('frame_id').absolute_delta.mean()
    representative=(movement-movement.median()).abs().sort_index().sort_values(kind='stable').index[0] if len(movement) else None
    bycondition=read(RESULTS/'statistics/statistical_status.json')
    complete_labels={label:int((complete.true_label==value).sum()) for label,value in [('phishing',1),('legitimate',0)]}
    summary={'status':'PRIMARY_FAILED_COMPLETENESS_EXPLORATORY_AVAILABLE_PAIRS_COMPLETED','run_id':read(CONFIG/'protocol.json')['run_id'],'new_downloaded_sms_records':0,'existing_raw_records_rescanned':67380,'new_lexical_uncertain_candidates':707,'rights_eligible_new_candidates':707,'source_reviewed_candidates':len(read(DATA/'review/final_source_decisions.json')),'source_frames':source['rows'],'source_labels':source['labels'],'origin_types':source['origins'],'template_families':source['families'],'initial_generations':frozen['initial_jobs'],'quality_retries':frozen['retry_jobs'],'generated_attempts':frozen['generated_attempts'],'approved_pairs':frozen['approved_pairs'],'rejected_or_unresolved_initial_slots':frozen['initial_jobs']-frozen['approved_pairs'],'approved_conditions':frozen['approved_conditions'],'complete_cases':complete_labels,'complete_cases_total':len(complete),'prompt_registry_sha256':file_sha(CONFIG/'PROMPT_REGISTRY.csv'),'models':models['models'],'threshold_crossings_available_by_model':{n:int((d[d.condition.ne('C0')].threshold_transition.isin(['0->1','1->0'])).sum()) for n,d in pred.items()},'extreme':extreme,'representative_frame_id':representative,'calls':calls,'primary_stronger_pilot_target_met':all(v>=30 for v in complete_labels.values()),'temporal_status':'Historical v3 NOT_RUN; no new temporal experiment','historical_v3_status':'unchanged, not pooled','stats_status':bycondition['status']}
    immutable_json(RESULTS/'SUMMARY.json',summary)
    # Exact generation-level lineage, including failed and superseded attempts.
    decisions=read(DATA/'review/rewrite_decisions.json');registry=csv_rows(CONFIG/'PROMPT_REGISTRY.csv')
    lineage=[]
    for d in decisions:
        g=d['generation'];p=next(r for r in registry if r['purpose']=='generation' and r['condition']==d['condition'])
        h=g['evidence_request_sha256'] if g else ''
        response=DATA/f'generated/calls/G_{h}.response.json'
        lineage.append({'frame_id':d['frame_id'],'condition':d['condition'],'attempt':d['attempt'],'prompt_version':p['version'],'prompt_sha256':p['sha256'],'generator_model':ROLES['G'],'generator_config_hash':file_sha(CONFIG/'generator_config.json'),'request_sha256':h,'response_sha256':read(response)['response_sha256'] if response.exists() else '', 'parsed_variant':g['text'] if g else '', 'timestamp':g['review_timestamp'] if g else '', 'status':'approved' if d['approved'] else 'rejected_or_missing','raw_request':f'data/benchmark_v3_2/generated/calls/G_{h}.request.json' if h else 'see initial/retry jobs and failed PROMPT_LOG call','raw_response':str(response.relative_to(ROOT)) if response.exists() else ''})
    table(RESULTS/'tables/generation_lineage.csv',lineage)
    table(RESULTS/'tables/source_composition.csv',[{'source_dataset':s,'label':l,'origin_type':o,'N':len(g)} for (s,l,o),g in pd.DataFrame(sources).groupby(['source_dataset','validated_label','origin_type'])])
    # Stage ledger is reconstructed from actual preserved request timestamps/file mtimes.
    protocol=read(CONFIG/'protocol.json');stages=[]
    for stage,path,note in [('protocol_freeze',CONFIG/'pre_scoring_freeze.json','Exact prompts, SAP, models before scoring'),('source_validation',DATA/'frozen/source_manifest.json','Includes original failures, one technical recovery and source-content exclusions; raw calls authoritative'),('generation_review',DATA/'frozen/matrix_manifest.json','At most one quality retry, every actual variant A/B reviewed'),('scoring',RESULTS/'predictions/prediction_manifest.json','Frozen models only; no fitting'),('statistics',RESULTS/'statistics/statistical_status.json','Complete and available cohorts separate'),('figures',RESULTS/'FIGURE_CATALOG.md','Exact data and metadata exported')]:
        stages.append({'run_id':protocol['run_id'],'phase':'C','experiment':stage,'dataset_version':'v3.2','prompt_version':'v1','model_version':'v3_final_primary_frozen','started':protocol['created_at'],'completed':mtime(path),'status':'EXPLORATORY','input_hash':file_sha(CONFIG/'pre_scoring_freeze.json'),'output_hash':file_sha(path),'notes':note+'; non-API start is protocol lower bound, completion is observed artifact mtime'})
    write_csv(RESULTS/'EXPERIMENT_LEDGER.csv',stages)
    changelog=[{'timestamp':source['frozen_at'],'change':k,'old_count':old,'new_count':new,'reason':reason,'affected_source':affected,'affected_labels':label,'affected_split':'robustness_only; original fitting splits unchanged','scientific_impact':impact} for k,old,new,reason,affected,label,impact in [
        ('new source acquisition',0,0,'No new rights-cleared English institutional-control release established','external discovery','all','No invented access or license'),
        ('expanded local candidate scan',0,707,'Broader literal finance vocabulary across67380existing records','NUS/Mendeley/UCI','uncertain','Candidates not approved controls'),
        ('rights exclusion','unknown',0,'Portuguese, unlicensed, synthetic or wrong-channel discoveries excluded','MOZ/revisedIndian/syntheticpayment/email','all','No guessed reuse grant'),
        ('ambiguous source ID removal',709,707,'NUS18088has2distincttexts; both excluded before API','NUS','uncertain','Initial packet archived'),
        ('family/training exclusion',12954,1065,'Global family isolation; bounded400additionalphishing candidate search','all','all','No fitting-data robustness evaluation'),
        ('source semantic validation',1065,16,'A/B and J plus preserved technical recovery','all','all','Machine approvals, not human truth'),
        ('source policy eligibility',16,12,'Fourpre-generationcontentexclusions; no label flips','NUS/Gateway','all','Preliminaryfreeze preserved'),
        ('balancing cap',12,source['rows'],'Fixed hash selection max100perclass; no manufactured controls','all','all','Class imbalance reported'),
        ('split changes',0,0,'No model split changed','all','all','Reuse primary models only')]]
    table(DOCS/'DATASET_CHANGELOG.csv',changelog)
    # table() already writes the paired Markdown; do not write a second variant.
    history=[dict(version='v1',dataset_size='143 verified historical phishing pairs; control denominator see original report',phishing='143paired',legitimate='not comparable here',models='LR/RF',conditions='paired original/rewrite',complete_trajectories='not the v3.2 definition',threshold_crossings='see preserved v1 evidence',main_result='Historical recall drop about0.6993percentagepoints; not rerun',major_limitation='Different protocol/population',what_changed_next='Prospective multi-condition design'),dict(version='v2.1 automated pilot',dataset_size='4sources/20available rows',phishing=2,legitimate=2,models='LR/RF',conditions='C0-C6; C2missing',complete_trajectories=0,threshold_crossings=0,main_result='Primary completeness failed; exploratory only',major_limitation='Synthetic legitimate controls and source-label confounding',what_changed_next='Real-source v3 acquisition'),dict(version='v3 final_run',dataset_size=195,phishing=186,legitimate=9,models='LR/RF/ModernBERT actually fine-tuned',conditions='C0/C1/C4/C5/C6',complete_trajectories='7phishing/0legitimate',threshold_crossings='0on39approvedpairs',main_result='39pairs, conditioncounts8/11/10/10; exploratory',major_limitation='One negative test control, retrospective corrections',what_changed_next='Newv3.2 prompts/source-review/generation; no pooling'),dict(version='v3.2',dataset_size=source['rows'],phishing=source['labels'].get('phishing',0),legitimate=source['labels'].get('legitimate',0),models='same frozen v3 primary models',conditions='C0/C1/C4/C5/C6',complete_trajectories=canonical(complete_labels),threshold_crossings=canonical(summary['threshold_crossings_available_by_model']),main_result='See new SUMMARY and paired tables only',major_limitation='Legitimate control target unmet; automated labels',what_changed_next='Independent real controls and fresh research cohort')]
    immutable_text(DOCS/'RESULTS_CHANGELOG.md','# Results changelog — incompatible versions are not pooled\n\n'+markdown(history)+'\nHistorical references: docs/benchmark_v3/FINAL_REPORT.md and docs/benchmark_v2_1/AUTOMATED_PILOT_FINAL_REPORT.md; v1 numbers are prior observations reported there, not new inference.\n')
    immutable_text(DOCS/'PHASE_MAP.md','# Phase map\n\n'+markdown([
        {'Phase':'A','Research question':'Original detection','Input dataset':'Preserved v3 final_run','Models':'LR/RF/ModernBERT','Prompts':'Historical only','Outputs':'Existing final_run experimentA','Current status':'Completed historical exploratory','Relationship to prior versions':'Read-only reference, no rerun or pooling'},
        {'Phase':'B','Research question':'Source generalization','Input dataset':'Preserved Gateway167phishing-only test','Models':'Separate v3 source-fitted LR/RF/ModernBERT','Prompts':'Historical only','Outputs':'Existing final_run experimentB','Current status':'Completed historical; temporal not run','Relationship to prior versions':'Not universal model ranking'},
        {'Phase':'C','Research question':'Intent/action-preserving linguistic robustness','Input dataset':'Newv3.2 source and rewrite freezes','Models':'Reused read-only v3 primary models','Prompts':'External v1 source3/generation4/rewrite3','Outputs':'Newv3.2 predictions/statistics/figures','Current status':summary['status'],'Relationship to prior versions':'New protocol/run; old39pairs unchanged and not merged'}]))
    limitations='''## Dataset limitations
Only one eligible legitimate source remains; its sender authenticity/origin is unresolved. Known real-source provenance is not proof of bank authorship. Rights-cleared does not establish label truth. Source imbalance, conservative family exclusions and finite candidate search limit population coverage.
## Model limitations
Reuse of small, imbalanced v3-trained models; probability outputs are uncalibrated. This experiment does not retrain or improve detectors. Frozen-artifact identity does not imply deployment quality.
## Generation limitations
Four conditions can overlap in actual surface changes; exact institution/numeric/placeholders constrain transformations. Rejected attempts and selective completeness produce survivorship effects. No outcome-driven rewrite optimization.
## Automated review limitations
Separate contexts are not statistically independent human annotation. Shared provider/model biases remain; generator and A share a snapshot. Confidence is subjective. Four initial source approvals required source-only policy exclusion, demonstrating fallibility.
## Statistical limitations
Below30legitimateframes, no adequately supported between-class or model-by-condition population comparison. Frame bootstrap cannot create support, and a degenerate interval on one control is not certainty. Conditions are repeated within frames; primary and available-pair cohorts differ.
## External validity limitations
Defanged public historical SMS are not representative current bank traffic. Prior pool inspection and review failures affect selection. No deployment FPR, temporal drift or universal model ranking.
## Causal inference limitations
Descriptive associations between surface distance and score movement do not establish linguistic causality. Semantic preservation is model-judged, not independently verified ground truth; no numeric semantic embedding similarity was measured.
'''
    immutable_text(DOCS/'LIMITATIONS.md','# Limitations from actual evidence\n\n'+limitations)
    immutable_text(DOCS/'DATA_QUALITY_REPORT.md','# Data quality report\n\n'+markdown(csv_rows(RESULTS/'tables/source_composition.csv'))+f'\nFinal source count {source["rows"]}; labels {source["labels"]}; origins {source["origins"]}. Template representatives {source["families"]}; all training/validation family overlaps excluded. No synthetic controls. English/SMS and financial function assessed in raw A/B/J source reviews. Source license evidence retained in SOURCE_EXPANSION_AUDIT.md. Duplicate and family edges preserved; old/new source count units are not interchangeable. Initial ambiguous NUS ID excluded. Sender authenticity remains unverified.\n\n'+limitations)
    primary_table=pd.read_csv(RESULTS/'tables/condition_performance.csv').to_dict('records')
    associations=csv_rows(RESULTS/'statistics/distance_associations.csv')
    comparison='# Model comparison\n\nPrimary complete-case estimates, with separate class denominators:\n\n'+markdown(primary_table)+'\n\nDistance association (frame-level exploratory):\n\n'+markdown(associations)+'\n\nHistorical v3A: all3predictphishing on29testmessages, F1=.982456 and FPR1/1; constant-phishing matches threshold metrics. Historical v3B: LR/RF167/167, separately fitted ModernBERT147/167 onselectedGatewayphishingonly; no legitimate source-test FPR. These historical A/B outcomes are not rerun or universal rankings. New C probability differences and threshold stability have different meanings: unchanged decisions can coexist with score movement and pre-existing false positives.\n'
    immutable_text(RESULTS/'MODEL_COMPARISON.md',comparison)
    status_text=f'**{summary["status"]}**. Preferred100+100 and minimum30+30 not achieved. New C has {source["labels"]}, complete trajectories {complete_labels}, {frozen["approved_pairs"]} approved rewrite pairs. Prior v3 final_run is untouched.'
    primary_results=markdown(primary_table)
    sections=[('Research questions','RQ-C1 recall change; C2 largest probability movement; C3 crossings; C4 distance association; C5 model decision stability; C6 class-specific sensitivity; C7 new versus existing false positives. All answered conditionally below; inadequate controls leave general questions unresolved.'),('Relationship to v1/v2/v3','See RESULTS_CHANGELOG.md. Do not pool historical protocols; old v3 remains195sources/39pairs/7phishingcomplete/0legitimatecomplete/0crossings.'),('Phase architecture','See PHASE_MAP.md: A/B are historical read-only references; v3.2 expands C only.'),('Source acquisition','67380existing raw records rescanned;707newuncertainlexicalcandidates, not707controls. No newly downloaded SMS dataset established. 23additionalphishingcandidates survived a bounded400candidate family-screen search. SOURCE_EXPANSION_AUDIT.md holds original rights discovery and exclusions.'),('Rights and provenance',markdown(csv_rows(RESULTS/'tables/source_composition.csv'))+'\nKnownNUSauthorunlimited-use declaration, Mendeley/UCI CC BY4 and Gateway MIT data release. Sting9 not retried without new access/rights evidence. No bypass or invented credentials.'),('Cohort construction',status_text+'\nTraining/validationexact/template exclusions and source-only hash sampling preceded generation; no new split or model fitting. Finite source search does not prove this is the largest possible worldwide cohort.'),('Source review',f'{len(read(DATA/"review/final_source_decisions.json"))}distinctcandidates reviewed through separate A/B contexts and J where eligible. Fourpre-generationpolicyexclusions are documented, not label flips. Twelve original connection failures and their one-time technical recoveries are preserved. Source decisions reconstruct exact raw provider outputs.'),('Prompt design',f'Tenexactv1promptfiles: sourceA/B/J, generationC1/C4/C5/C6, rewriteA/B/J. Registry SHA256 {summary["prompt_registry_sha256"]}. PROMPT_CHANGELOG.md records prospective v3.2 distinctions. No detector-result-driven prompt change.'),('Generation',f'Frames{source["rows"]}; initialjobs{frozen["initial_jobs"]}; qualityretries{frozen["retry_jobs"]}; actualgeneratedattempts{frozen["generated_attempts"]}. At most1qualityretry for deterministic unchanged/malformed/invariantfailure; technical missing generation receipts never become quality retries. Everyattemptretained.'),('Rewrite review',f'Approvedpairs{frozen["approved_pairs"]}; rejected/unresolvedinitialslots{frozen["initial_jobs"]-frozen["approved_pairs"]}; conditionapprovals{frozen["approved_conditions"]}. Everyactuallygeneratedattempt receives deterministic plus A/B semantic review; Jresolvesboolean disagreements. Allsemanticgates/thresholdconfidence>=.8required, no detector feedback.'),('Manipulation validation','See manipulation/condition_summary and condition_overlap. Actual C6>C1ordering is measured, notforced. Lexical TF-IDFcosine is not semantic similarity; semantic_similarity_if_available is blank. Binary reviewer approval is explicitly distinct from numerical semantic closeness.'),('Model freeze',markdown(models['models'])+'\nModels and SAP froze before new generation/scoring; no retraining. ModernBERT was actuallyfine-tuned inpreservedv3; this phaseonlyinfers.'),('Phase A reference','Historicalonly: all3models TP28/FP1/TN0/FN0 on29messages, F1 .982456 and solelegitimate falsepositive. No new detection benchmark.'),('Phase B reference','Historicalonly: LR/RFrecall1, ModernBERT147/167=.880240 onGatewayphishing-only. NoFPR/temporal claim; do notuniversallyrank models.'),('Phase C primary results',primary_results+'\nMainconditioncomparisons use onlyapprovedcompleteframes; available_pair_metrics is separate. Belowminimumcontrols, allinferenceexploratory.'),('Legitimate controls',f'EligiblelegitimateC0={source["labels"].get("legitimate",0)}, completelegitimate={complete_labels["legitimate"]}. No syntheticremainder. Onecard-registrationfraud-alertsource cannotestimatebankingpopulationFPR or between-classsensitivity.'),('Threshold transitions',markdown(csv_rows(RESULTS/'tables/false_positive_transitions.csv'))+f'\nAvailablepaircrossingspermodel={summary["threshold_crossings_available_by_model"]}. ExistingC0falsepositives are distinct from newlycreatedfalsepositives and recoveries; no missing-condition-as-zero interpretation.'),('Distance analysis',markdown(associations)+'\nPerframeslopes and bootstrap describe selectedcompleteframes, notlinguisticcausality.'),('Model comparison','See MODEL_COMPARISON.md, secondary_tests and class-separatedmodel_condition_effects. Probabilitymovementandclassificationstabilitydiffer. Nosingleuniversalbestmodel supported.'),('Statistical inference','PrescoringSAP frozen;24primaryMcNemar/Holm tests and24secondarypairedmodelcontrasts, framebootstrap2000seed42. Allstatistics exploratory. Insufficientgroups have undefinedquantities, notinventedzeroeffects. No justifiedpopulationmixedmodel inthis tinycontrolsample.'),('Extreme cases',canonical(extreme) if extreme else 'No approvedpair available; extremecaseundefined.'),('Representative case',f'Frame{representative}; predefinednearestmedianframe-meanabsolutemovement acrossallmodels/fourconditions amongcompleteframes. Separatefromstrongestavailablepair.'),('Limitations',limitations),('Safe claims','An additive detector-blind rewrite protocol was executed with exact prompt/call/source/model evidence. Conditional paired observations may be presented with actual N; no balanced-pilot success.'),('Unsafe claims','Do notclaim30+30/100+100completion, independenthumangroundtruth, real-worldFPR, semanticcausality, populationrobustness, detectorimprovement or universalModernBERTsuperiority.'),('What changed from previous run','Newsourceaudit, explicitexternalprompts, freshC0metadatareviews, prospectiveSAP, newgeneration/reviewevidence, samefrozenv3primarymodels. Old39pairs/countsremainunchanged. Fourinitialsourcepolicyerrors and ambiguousnativeID documentedbeforegeneration; no silentcorrections.'),('Recommended next work','Acquire rights-cleared real institutional financial controls with independenthumanadjudication and new familydiversity. Do not scale uncertaincontrols, repeatgeneration toobtaininteresting scores, or regardgreenengineeringtests as scientificvalidation.')]
    # Presentation prose is separate from exact machine identifiers and numeric tables.
    available_effects=csv_rows(RESULTS/'statistics/available_pair_probability_effects.csv')
    available_associations=csv_rows(RESULTS/'statistics/available_pair_distance_associations.csv')
    available_transitions=csv_rows(RESULTS/'tables/available_pair_false_positive_transitions.csv')
    sections=[
        ('Research questions','RQ-C1 asks whether recall changes; C2 which condition moves probabilities most; C3 which causes crossings; C4 how surface distance accompanies movement; C5 whether model decisions differ in stability; C6 whether classes differ; C7 whether false positives are created or recovered. Zero complete cases leave the primary questions unanswered. Available-pair descriptions below are conditional observations.'),
        ('Relationship to v1/v2/v3','Historical protocols remain separate. Preserved v3 final_run has195 sources,186 phishing,9 legitimate,39 approved rewrite pairs,7 complete phishing trajectories,0 complete legitimate trajectories and0 observed crossings. Nothing from this new run is merged into those numbers. See RESULTS_CHANGELOG.md.'),
        ('Phase architecture','A: historical original-message detection. B: historical source generalization, with a single-class Gateway test. C: this additive rewrite experiment. See PHASE_MAP.md. A/B were not rerun or used to tune the new rewrites.'),
        ('Source acquisition','Rescanned67,380 existing raw records across NUS, Mendeley and UCI. Expanded lexical screening found707 new uncertain candidates; these are not707 legitimate controls. No new SMS release with established English institutional-control rights was acquired. Another23 candidates survived a bounded400-candidate phishing-family screen. See SOURCE_EXPANSION_AUDIT.md and its primary-source evidence.'),
        ('Rights and provenance',markdown(csv_rows(RESULTS/'tables/source_composition.csv'))+'\nNUS author unlimited-use declaration, Mendeley/UCI CC BY4 and Gateway MIT data release are distinct rights bases. Real-source origin means observed source provenance, not authenticated bank authorship. Synthetic primary controls were not added. Sting9 was not accessed without newly established access and rights.'),
        ('Cohort construction',status_text+'\nEvery C0 was screened against primary v3 fitting and validation exact/template families. Sampling uses source-only fixed hash order. Models and splits remain unchanged. The finite inspected pool is not proof that no additional valid public source exists.'),
        ('Source review','Reviewed1,065 distinct source candidates with separate A/B contexts and adjudication where eligible. Sixteen automatic approvals preceded four documented source-policy exclusions, leaving12 C0 sources. Twelve connection failures received at most one technical recovery with identical payloads; original failures remain preserved. Four exclusions changed eligibility, not class labels. These judgments are automated, not independent human annotation.'),
        ('Prompt design',f'Ten exact external v1 prompts were frozen before scoring: source A/B/J, generation C1/C4/C5/C6 and rewrite A/B/J. Registry SHA-256: {summary["prompt_registry_sha256"]}. No prompt or model was changed using detector results. See PROMPT_CHANGELOG.md.'),
        ('Generation',f'{source["rows"]} frames yielded {frozen["initial_jobs"]} initial jobs and {frozen["retry_jobs"]} permitted quality retries, with {frozen["generated_attempts"]} actual generated attempts. Retries addressed deterministic quality failures only. Missing technical generation evidence never authorizes a quality retry. Failed outputs and reasons remain in attempts.csv and raw calls.'),
        ('Rewrite review',f'{frozen["approved_pairs"]} condition pairs were approved; {frozen["initial_jobs"]-frozen["approved_pairs"]} initial slots remained rejected/unresolved. Approval counts: {frozen["approved_conditions"]}. Every actual attempt received deterministic and A/B semantic review; J addressed boolean disagreements. Semantic acceptance cannot override literal or condition failures. No further regeneration was used to manufacture completeness.'),
        ('Manipulation validation','All approved variants have Jaccard, normalized edit, frozen lexical TF-IDF cosine and prespecified surface-distance measurements. Condition overlap and failures are saved. C6 versus C1 ordering is measured rather than forced. Numerical semantic similarity is unavailable; binary review approval is not embedding similarity. Zero complete cases prevent a primary all-condition manipulation claim.'),
        ('Model freeze',markdown(models['models'])+'\nThe unchanged v3 primary models were frozen before new generation. ModernBERT was actually fine-tuned in v3; v3.2 only performs frozen inference. No model retraining or tuning occurred.'),
        ('Phase A reference','Historical v3 only: all three models had TP28, FP1, TN0 and FN0 on29 messages. F1=.982456 coexisted with failure on the sole legitimate control. A constant-phishing classifier matches these threshold metrics. This is not a new detection benchmark.'),
        ('Phase B reference','Historical v3 only: LR/RF detected167/167 Gateway phishing messages; separately fitted ModernBERT detected147/167. This selected, single-class source test supports no legitimate FPR, temporal robustness or universal ranking.'),
        ('Phase C primary results','**NOT RUN: zero complete C0/C1/C4/C5/C6 trajectories.** Primary metrics and24 planned paired p-values are undefined, not zero effects or nonsignificance.\n\n'+primary_results+'\n\nAvailable-pair metrics are separately saved in available_pair_metrics.csv. Their condition cohorts differ.'),
        ('Legitimate controls',f'Only {source["labels"].get("legitimate",0)} legitimate C0 and {complete_labels["legitimate"]} complete legitimate trajectories survive. The named card-registration fraud alert has intelligible financial function, but sender authenticity is unverified. Its rewrites cannot create independent control messages or support population FPR.'),
        ('Threshold transitions',markdown(available_transitions)+f'\nAvailable-pair crossing counts per model: {summary["threshold_crossings_available_by_model"]}. Existing C0 false positives, newly created false positives and recoveries are separate quantities. Primary transition tables have no supporting complete frames; their zero counts are not observed primary stability.'),
        ('Distance analysis','Primary distance association is unavailable. Separately labelled available-pair frame slopes follow; frames need at least two varying approved rewrites.\n\n'+markdown(available_associations)+'\nNo association establishes linguistic causality. Missing conditions and selected approvals constrain interpretation.'),
        ('Model comparison','No primary model-by-condition comparison is estimable. Available-pair score effects are descriptive and class-specific:\n\n'+markdown(available_effects)+'\nProbability movement and threshold stability answer different questions. No universal best model follows.'),
        ('Statistical inference','The SAP froze before scoring:24 primary McNemar/Holm hypotheses and24 secondary paired-model contrasts, with frame bootstrap2,000 draws and seed42. With no complete cases, primary tests and model interactions are NOT RUN. Available-pair intervals remain exploratory; one-frame support is not converted into a population confidence claim.'),
        ('Extreme cases','The strongest individual available-pair movement is explicitly an extreme, not representative:\n\n'+(canonical(extreme) if extreme else 'Unavailable: no approved pair.')),
        ('Representative case','**Unavailable:** no complete frame exists for the prespecified nearest-median complete-trajectory selection rule. Figure9 is an annotated unavailable result, not an invented or incomplete primary trajectory.'),
        ('Limitations',limitations),
        ('Safe claims','A separate detector-blind protocol was executed with exact source, prompt, request, review, model and prediction evidence. Its cohort and completeness targets failed. Selected available-pair changes can be described with actual N, without calling the primary experiment successful.'),
        ('Unsafe claims','Do not claim30+30 or100+100 completion, independent human truth, primary significance, general robustness, current banking FPR, causal linguistic effects or contextual-model superiority. Missing conditions are not zero effects.'),
        ('What changed from previous run','New source screening, prospective external prompts and SAP, fresh generation/review calls and separately versioned results were added. Existing v3 data, models, outputs and FINAL_REPORT.md are unchanged. The ambiguous native ID and four source-policy exclusions were documented before generation. No old39-pair result was reinterpreted.'),
        ('Recommended next work','Acquire rights-cleared real institutional controls with independent human adjudication and new family diversity. Prospectively redesign the generation instrument after examining preserved condition failures, then start a new frozen run. Do not relax this run’s acceptance rules or repeat it until desired completeness or scores appear.')]
    final='# Benchmark v3.2 final report\n\n'+status_text+'\n'+''.join(f'\n## {i}. {title}\n\n{body}\n' for i,(title,body) in enumerate(sections,1))
    immutable_text(DOCS/'FINAL_REPORT.md',final)
    presentation='# Presentation summary\n\n## Phase A — Detection\n\nClaim: Historicalv3allmodels failedsolelegitimatecontrol.\nExact value: F1 .982456, FPR1/1.\nN:29testmessages,28phishing/1legitimate.\nEvidence: docs/benchmark_v3/FINAL_REPORT.md, preservedfinal_run tables04/08.\nPlain-language meaning: HighF1 masksfailureonnegativecontrol.\nLimitation: Onecontrol andautomatedlabels.\nSafe wording: Inthisselectedhistoricaltestall3madeidenticalthresholddecisions.\nUnsafe wording: DetectorsareaccurateforbankingSMS.\n\n## Phase B — Generalization\n\nClaim: HistoricalselectedGatewayrecalldiffers.\nExact value: LR/RF167of167; ModernBERT147of167.\nN:167phishing,0legitimate.\nEvidence: preservedv3final_run table05.\nPlain-language meaning: Conditionalphishing-onlysourceresult.\nLimitation: Singletestclassandseparatelyfittedmodels.\nSafe wording: Thisselectedsourceexperimenthadtheseobservations.\nUnsafe wording: Universallexicalmodel superiority.\n\n## Phase C — AI Rewrite Robustness\n\n'+status_text+'\n\nClaim: Conditionalpairedrewritestability.\nExact value: '+canonical(summary['threshold_crossings_available_by_model'])+f' crossings over{frozen["approved_pairs"]}availablepairs/model.\nN: complete{canonical(complete_labels)}; pairedvariantsarenotindependentsources.\nEvidence: predictions/*_predictions.csv, tables/condition_performance.csv, tables/false_positive_transitions.csv, statistics/primary_tests.csv.\nPlain-language meaning: Decisionchangesandscoremovementmustbereportedseparately.\nLimitation: Controlminimumunmet, automatedreviewandselectiveattrition.\nSafe wording: Ontheseapprovedpairedmessages, theobservedtransitionsareasshown.\nUnsafe wording: Broadrobustness, bankFPRorcausalmodelranking.\n\n'+primary_results+'\n\nLargestavailablepair: '+canonical(extreme)+'\n\nEveryprimaryN/ratecanbetracedthroughRESULT_EVIDENCE_INDEX.csv; figureexplanationsareinPRESENTATION_GRAPH_NOTES.md.\n'
    # Keep prose readable without changing exact identifiers in source artifacts.
    presentation='''# Presentation summary

## Phase A — Detection (historical v3)

Claim: All three models failed the sole legitimate test control.
Exact value: F1 .982456; FPR1/1.
N:29 messages,28 phishing and1 legitimate.
Evidence: preserved v3 final_run tables04/08 and FINAL_REPORT.md.
Plain-language meaning: High F1 can mask failure on the minority class.
Limitation: One negative and automated labels.
Safe wording: The selected historical test produced these decisions.
Unsafe wording: The models reliably distinguish legitimate banking SMS.

## Phase B — Generalization (historical v3)

Claim: Selected Gateway phishing recall differed.
Exact value: LR/RF167/167; separately fitted ModernBERT147/167.
N:167 phishing messages,0 legitimate.
Evidence: preserved v3 final_run table05.
Plain-language meaning: This is a conditional single-source recall observation.
Limitation: No legitimate source-test controls, no temporal experiment.
Safe wording: This selected source experiment had the reported recall.
Unsafe wording: Lexical models are universally superior.

## Phase C — AI Rewrite Robustness (new v3.2)

'''+status_text+f'''

Claim: The primary complete-trajectory experiment failed completeness.
Exact value:0 complete phishing and0 complete legitimate trajectories.
N:{source['rows']} sources; {frozen['initial_jobs']} initial jobs; {frozen['approved_pairs']} approved pairs after {frozen['retry_jobs']} quality retries.
Evidence: frozen/matrix_manifest.json, attempts.csv, statistics/statistical_status.json.
Plain-language meaning: No source has all four approved rewrite conditions.
Limitation: One legitimate source and selective attrition; no primary inference.
Safe wording: The protocol produced selected available pairs but no complete trajectory.
Unsafe wording: A scientifically adequate expanded robustness pilot succeeded.

Claim: Available-pair threshold transitions are conditional observations.
Exact value: {canonical(summary['threshold_crossings_available_by_model'])} crossings by model.
N:{frozen['approved_pairs']} available pairs per model; these repeat source frames.
Evidence: predictions/*_predictions.csv and tables/available_pair_false_positive_transitions.csv.
Plain-language meaning: Score movement can occur with or without decision changes; existing false positives are distinct from new ones.
Limitation: Available condition cohorts differ; one control cannot establish FPR.
Safe wording: On these approved pairs, the observed transitions are those saved in the paired tables.
Unsafe wording: Missing conditions establish stability or a detector’s general robustness.

Primary metrics are unavailable. Available-pair class-specific rates:\n\n'''+markdown(csv_rows(RESULTS/'tables/available_pair_metrics.csv'))+'\n\nEvery table value has a coordinate in RESULT_EVIDENCE_INDEX.csv. See PRESENTATION_GRAPH_NOTES.md for figure explanations.\n'
    immutable_text(RESULTS/'PRESENTATION_SUMMARY.md',presentation)
    # Every aggregate table and figure number receives a direct source coordinate.
    index=[];analytical=list((RESULTS/'tables').glob('*.csv'))+list((RESULTS/'statistics').glob('*.csv'))+list((RESULTS/'figures').glob('*_data.csv'))+[RESULTS/'manipulation/condition_summary.csv']
    for p in sorted(analytical):
        rows=csv_rows(p)
        for i,r in enumerate(rows,2):
            for col,val in r.items():
                try:float(val)
                except (TypeError,ValueError):continue
                index.append({'result_id':sha(str(p.relative_to(ROOT))+f':{i}:{col}')[:20],'claim':f'{p.stem}, CSV row{i}, {col}','value':val,'unit':'as defined by source column','population':str(r.get('true_label',r.get('cohort','selected run frames'))),'N':r.get('N_frames',r.get('N','see row support columns')),'source_file':p.relative_to(ROOT).as_posix(),'source_columns':f'row={i};column={col}','analysis_script':'src/benchmark_v3_2/analysis.py or figures.py or reports.py','figure_or_table':p.stem,'statistical_test':r.get('analysis_id','descriptive'),'limitations':'Exploratory machine-reviewed sample; class support and repeated frame caveats','safe_to_present':str(np.isfinite(float(val)))})
    write_csv(RESULTS/'RESULT_EVIDENCE_INDEX.csv',index)
    catalog=[]
    for p in sorted(list((RESULTS/'tables').glob('*.csv'))+list((RESULTS/'statistics').glob('*.csv'))+list((RESULTS/'manipulation').glob('*.csv'))):
        rows=csv_rows(p);catalog.append({'file':p.relative_to(RESULTS).as_posix(),'purpose':p.stem.replace('_',' '),'source_data':'Frozen source/matrix and predictions; exact references in evidence index','N':len(rows),'interpretation':'Rows are table records, not necessarily independent frames; use explicit support columns. Exploratory only.'})
    immutable_text(RESULTS/'TABLE_CATALOG.md','# Table catalog\n\n'+markdown(catalog))
    try:git_commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True,stderr=subprocess.DEVNULL).strip()
    except Exception:git_commit='unavailable'
    manifest_path=RESULTS/'RUN_MANIFEST.json';completed=read(manifest_path)['completed_at'] if manifest_path.exists() else now()
    outputs={str(p.relative_to(ROOT)).replace('\\','/'):file_sha(p) for p in sorted(RESULTS.rglob('*')) if p.is_file() and p.name not in {'RUN_MANIFEST.json','verification.json'}}
    immutable_json(manifest_path,{'run_id':protocol['run_id'],'started_at':protocol['created_at'],'completed_at':completed,'git_commit':git_commit,'config_hash':file_sha(CONFIG/'protocol.json'),'prompt_registry_hash':summary['prompt_registry_sha256'],'dataset_hash':frozen['matrix_sha256'],'model_hashes':{r['model_name']:r['sha256'] for r in models['models']},'statistical_plan_hash':file_sha(DOCS/'STATISTICAL_ANALYSIS_PLAN.md'),'outputs':outputs,'status':summary['status'],'source_only_prescore_amendments':['CORRECTION_20261107_PRE_SOURCE_API.md','CORRECTION_20261107_PRE_GENERATION_ELIGIBILITY.md','source_technical_recovery_v1.json']})
    print(json.dumps(summary,indent=2,default=str),flush=True)
    return summary

if __name__=='__main__':reports()
