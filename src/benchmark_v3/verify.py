"""Final read-only audit of corrected evidence, training/splits and outputs."""
from collections import Counter
import json
import numpy as np
import pandas as pd
import joblib
from sklearn.feature_extraction.text import TfidfVectorizer
from .core import ROOT,DATA,MODELS,RESULTS,CONFIG,read_json,file_digest,verify_hash,save_json,assert_blind,leakage_errors
from .correction import CD,CM,CR,activate,corrected_structural_text
from . import cohort as grouping
from .baselines import probabilities
from .evaluation import metrics
from src.benchmark_v2_2.verify import verify_baseline


def verify():
    historical=verify_baseline(ROOT,ROOT/'docs/benchmark_v3/BASELINE_INVENTORY.csv')
    if CD.name=='final_run':
        from .final_run import verify_eligibility
        verify_eligibility()
    for record in read_json(DATA/'provenance/smish_dt_manifest.json')['files']:
        verify_hash(ROOT/'external/SMISH_DT'/record['path'],record['sha256'])
    # Source/rewrite evidence can be valid while a former train/test partition
    # is invalid. Verify raw stimulus bindings before activating corrected paths.
    from .robustness_evaluation import verify_supplement
    original_stimuli,_=verify_supplement()
    original=read_json(DATA/'frozen/cohort_manifest.json')
    if original['cohort_sha256']!='6ca8c803e02f3135f094cfc2cd42a7ea5f780047bfd5f049c890c4ba9ff2f0f3':raise ValueError('Invalidated run was modified')
    activate()
    from .protocol import verify_frozen_inputs
    freeze=verify_frozen_inputs('primary');verify_frozen_inputs('source_holdout')
    frame=pd.read_csv(CD/'frozen/modeling_cohort.csv',keep_default_na=False)
    source=pd.read_csv(CD/'frozen/source_holdout_cohort.csv',keep_default_na=False)
    if leakage_errors(frame.to_dict('records')) or leakage_errors(source.to_dict('records')):raise ValueError('Corrected split leakage')
    if frame.template_family_id.nunique()!=len(frame) or frame.id.nunique()!=len(frame):raise ValueError('Duplicate corrected representative')
    normal=frame.safe_text.map(corrected_structural_text)
    if normal.duplicated().any():raise ValueError('Exact corrected structural template duplicate')
    if sum(frame.id.isin(['mendeley-334','mendeley-1361']))>1:raise ValueError('Known payee template duplicate remains')
    if frame.id.isin(['mendeley-4','nus-5489']).any():raise ValueError('Policy-excluded personal coordination remains')
    for r in source[source.split.isin(['train','validation'])].to_dict('records'):
        if 'gateway' in json.loads(r['family_source_origins_json']):raise ValueError('Held-out source lineage enters fitting')
    candidates={r['id']:r for r in pd.read_csv(DATA/'candidates/permitted_financial_candidates.csv',keep_default_na=False,low_memory=False).to_dict('records')}
    decisions={r['id']:r for stage in ['controls','positives'] for r in pd.read_csv(DATA/f'review/{stage}_v3_1_decisions.csv',keep_default_na=False).to_dict('records')}
    for r in frame.to_dict('records'):
        result=grouping.verify_review(candidates[r['id']],decisions[r['id']])
        if not result['approved'] or result['annotation']['label']!=r['label']:raise ValueError('Corrected modeling label does not match actual review')
    for experiment,cohort in [('primary',frame),('source_holdout',source)]:
        expected=freeze['cohort_sha256' if experiment=='primary' else 'source_holdout_cohort_sha256']
        training=cohort[cohort.split.eq('train')];valid=cohort[cohort.split.eq('validation')]
        for model in ['modernbert' if experiment=='primary' else 'modernbert_source_holdout']:
            directory=CM/model;manifest=read_json(directory/'model_manifest.json')
            for p,h in manifest['files'].items():verify_hash(directory/p,h)
            config=read_json(directory/'training_config.json')
            if config['frozen_csv_sha256']!=expected or config['fitting_token_lengths']['count']!=len(training)+len(valid):raise ValueError('ModernBERT fitting cohort mismatch')
            if config['epochs']!=2 or config['learning_rate']!=2e-5 or config['random_seed']!=42:raise ValueError('ModernBERT fixed configuration changed')
        lexical=CM/experiment/'lexical';manifest=read_json(lexical/'model_manifest.json')
        if manifest['frozen_cohort_sha256']!=expected:raise ValueError('Lexical fitting cohort mismatch')
        expected_vectorizer=TfidfVectorizer(ngram_range=(1,2),max_features=20000,min_df=1).fit(training.safe_text)
        test=cohort[cohort.split.eq('held_out_test' if experiment=='primary' else 'source_test')]
        folder=CR/('experiment_A_detection' if experiment=='primary' else 'experiment_B_generalization')
        em=read_json(folder/'evaluation_manifest_all_models.json');verify_hash(folder/'predictions_all_models.csv',em['predictions_sha256'])
        preds=pd.read_csv(folder/'predictions_all_models.csv',keep_default_na=False)
        reported=pd.read_csv(folder/'metrics_all_models.csv',keep_default_na=False).set_index('model')
        for name in ['LR','RF','ModernBERT']:
            rows=preds[preds.model.eq(name)].set_index('id').loc[test.id]
            if rows.label.tolist()!=test.label.tolist():raise ValueError('Evaluation labels/IDs mismatch')
            if name in ['LR','RF']:
                record=manifest['models'][name];verify_hash(lexical/record['file'],record['sha256']);model=joblib.load(lexical/record['file'])
                tfidf=model.named_steps['tfidf']
                if tfidf.vocabulary_!=expected_vectorizer.vocabulary_ or not np.allclose(tfidf.idf_,expected_vectorizer.idf_):raise ValueError('Fitted TF-IDF differs from train-only reconstruction')
                if not np.allclose(probabilities(model,test.safe_text.tolist()),rows.probability,atol=1e-12):raise ValueError('Frozen lexical predictions not reproducible')
            y=test.label.map({'legitimate':0,'phishing':1});recomputed=metrics(y,rows.probability)
            for key in ['TP','FP','TN','FN','recall','F1','false_positive_rate']:
                value=reported.loc[name,key]
                if recomputed[key] is None:
                    if value!='':raise ValueError('Undefined metric was filled')
                elif not np.isclose(float(value),recomputed[key]):raise ValueError('Reported metric mismatch')
    cm=read_json(CD/'robustness/freeze_manifest.json');verify_hash(CD/'robustness/frozen_approved_variants.json',cm['frozen_sha256'])
    stimuli=read_json(CD/'robustness/frozen_approved_variants.json');ids=set(frame[frame.split.eq('held_out_test')].id)
    if stimuli!=[r for r in original_stimuli if r['frame_id'] in ids]:raise ValueError('Corrected stimuli changed or include training IDs')
    cs=read_json(CR/'experiment_C_robustness/analysis_summary.json');verify_hash(CR/'experiment_C_robustness/predictions.csv',cs['predictions_sha256'])
    cp=pd.read_csv(CR/'experiment_C_robustness/predictions.csv',keep_default_na=False)
    primary=pd.read_csv(CR/'experiment_A_detection/predictions_all_models.csv',keep_default_na=False)
    for name,part in cp.groupby('model'):
        base=part[part.condition.eq('C0')].set_index('frame_id')
        if not np.allclose(base.probability,base.original_probability,atol=1e-6):raise ValueError('C0 nonzero delta')
        comparison=primary[primary.model.eq(name)].set_index('id').loc[base.index]
        if not np.allclose(base.probability,comparison.probability,atol=1e-6):raise ValueError('C0 not identical to corrected model baseline')
        if not np.allclose(part.signed_delta,part.original_probability-part.probability,atol=1e-12):raise ValueError('Paired delta mismatch')
        if not np.allclose(part.absolute_delta,abs(part.signed_delta),atol=1e-12):raise ValueError('Absolute delta mismatch')
    roles=Counter();versions=Counter();usage=Counter();source_requests=list((DATA/'review/calls').glob('*.request.json'))
    for path in source_requests:
        request=read_json(path);assert_blind(json.loads(request['raw_request']['input']))
        roles['source_'+request['role']]+=1
        schema=request['raw_request']['text']['format']['schema']['properties']['items']['items']['properties']
        versions['v3.1' if 'nonoperational_text' in schema else 'v3.0_invalid_instrument']+=1
        result=read_json(path.with_name(path.name.replace('.request.json','.result.json')))
        u=result['raw_response'].get('usage',{})
        for key in ['input_tokens','output_tokens']:usage[key]+=u.get(key,0)
    supplement_requests=list((DATA/'robustness/calls').glob('*.request.json'))
    for path in supplement_requests:
        request=read_json(path);assert_blind(json.loads(request['raw_request']['input']));roles['supplement_'+request['role']]+=1
        response=read_json(path.with_name(path.name.replace('.request.json','.response.json')))
        for key in ['input_tokens','output_tokens']:usage[key]+=response['raw_response'].get('usage',{}).get(key,0)
    eligibility_requests=[]
    if CD.name=='final_run':
        eligibility_requests=list((DATA/'final_eligibility_audit/calls').glob('*.request.json'))
        for path in eligibility_requests:
            request=read_json(path);assert_blind(json.loads(request['raw_request']['input']));roles['eligibility_'+request['role']]+=1
            response=read_json(path.with_name(path.name.replace('.request.json','.response.json')))
            for key in ['input_tokens','output_tokens']:usage[key]+=response['raw_response'].get('usage',{}).get(key,0)
    figure_status=read_json(CR/'figures/figure_status.json')
    result={'status':'VERIFIED_CORRECTED_EXPLORATORY_RESULTS','authoritative_run':CD.name,'historical_files_checked':historical,'historical_files_changed':0,
      'original_run_status':'INVALIDATED_PRESERVED_TEMPLATE_LEAK','corrected_rows':len(frame),'corrected_labels':frame.label.value_counts().to_dict(),
      'corrected_source_holdout_phishing':int(sum(source.split=='source_test')),'known_payee_template_fixed':True,'source_holdout_origin_clear':True,
      'train_only_tfidf_reconstructed':True,'model_hashes_verified':True,'actual_source_and_rewrite_raw_evidence_verified':True,
      'source_provider_requests':len(source_requests),'supplement_provider_requests':len(supplement_requests),'provider_requests_by_role':dict(roles),'source_requests_by_instrument':dict(versions),'provider_usage':dict(usage),
      'final_eligibility_provider_requests':len(eligibility_requests),
      'supplement_scored_source_frames':cm['source_frames'],'supplement_scored_variants':cm['accepted_rewrites'],'supplement_complete_phishing_frames':len(cm['complete_core_frames']),
      'no_detector_feedback_in_requests':True,'figures':figure_status['scientific_figure_count'],'tables':figure_status['tables'],
      'independent_human_annotation':False,'desired_300_per_class_met':False,'confirmatory_claims_supported':False}
    save_json(CR/'verification.json',result);print(json.dumps(result,indent=2));return result


if __name__=='__main__':
    import argparse
    p=argparse.ArgumentParser();p.add_argument('--final',action='store_true');a=p.parse_args()
    if a.final:
        from . import correction,final_run
        CD=final_run.FD;CR=final_run.FR;CM=final_run.FM
        correction.CD=CD;correction.CR=CR;correction.CM=CM
    verify()
