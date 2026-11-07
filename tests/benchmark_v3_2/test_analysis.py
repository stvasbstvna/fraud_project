from pathlib import Path
import pandas as pd
import pytest


def fixture_files(tmp_path):
    rows = []
    for frame, label, primary in [('a', 0, True), ('b', 0, True), ('c', 1, True), ('d', 1, True), ('extra', 0, False)]:
        for condition in ['C0', 'C1', 'C4', 'C5', 'C6']:
            rows.append(dict(frame_id=frame, condition=condition, true_label=label, text='text', primary_complete_case=primary, source_dataset='fixture', template_family_id=frame, surface_distance=0 if condition=='C0' else 1))
    matrix = pd.DataFrame(rows)
    matrix.to_csv(tmp_path/'matrix.csv', index=False)
    predictions = tmp_path/'predictions'
    predictions.mkdir()
    for model in ['LR', 'RF', 'ModernBERT']:
        data = matrix[['frame_id','condition','true_label']].copy()
        data['prediction'] = [int(r.true_label) if r.condition=='C0' else 1-int(r.true_label) for r in matrix.itertuples()]
        data['probability'] = data.prediction * .8 + .1
        data.to_csv(predictions/f'{model}_predictions.csv', index=False)
    return tmp_path/'matrix.csv', predictions


def test_analysis_class_metrics_pairing_holm_and_idempotence(tmp_path):
    from src.benchmark_v3_2.analysis import analyze
    matrix, predictions = fixture_files(tmp_path)
    output = tmp_path/'out'
    analyze(matrix, predictions, output, bootstrap_replicates=50)
    tests = pd.read_csv(output/'statistics/primary_tests.csv')
    assert len(tests) == 24
    assert set(tests.N_frames) == {2}
    assert set(tests.raw_p) == {.5}
    assert set(tests.adjusted_p) == {1.0}
    metrics = pd.read_csv(output/'tables/primary_metrics.csv')
    row = metrics[(metrics.model=='LR') & (metrics.condition=='C1')].iloc[0]
    assert row.recall == 0 and row.false_positive_rate == 1
    assert row.N_frames == 4
    available = pd.read_csv(output/'tables/available_pair_metrics.csv')
    assert available.N_frames.max() == 5
    analyze(matrix, predictions, output, bootstrap_replicates=50)
    (output/'statistics/primary_tests.csv').write_text('changed')
    with pytest.raises(FileExistsError):
        analyze(matrix, predictions, output, bootstrap_replicates=50)


def test_undefined_metrics_remain_blank(tmp_path):
    from src.benchmark_v3_2.analysis import analyze
    matrix, predictions = fixture_files(tmp_path)
    data = pd.read_csv(matrix)
    data = data[data.true_label==0]
    data.to_csv(matrix,index=False)
    for file in predictions.glob('*.csv'):
        p = pd.read_csv(file)
        p[p.true_label==0].to_csv(file,index=False)
    analyze(matrix,predictions,tmp_path/'out',bootstrap_replicates=20)
    metrics=pd.read_csv(tmp_path/'out/tables/primary_metrics.csv')
    assert metrics.recall.isna().all()
    tests=pd.read_csv(tmp_path/'out/statistics/primary_tests.csv')
    assert tests.loc[tests.true_label==1,'raw_p'].isna().all()


def test_inconsistent_complete_case_flag_excludes_entire_frame(tmp_path):
    from src.benchmark_v3_2.analysis import analyze
    matrix, predictions = fixture_files(tmp_path)
    data = pd.read_csv(matrix)
    data.loc[(data.frame_id=='a') & (data.condition=='C6'), 'primary_complete_case'] = False
    data.to_csv(matrix,index=False)
    status=analyze(matrix,predictions,tmp_path/'out',bootstrap_replicates=20)
    assert status['primary_frames']==3


def test_sap_class_separated_absolute_contrasts_and_frame_slopes(tmp_path):
    from src.benchmark_v3_2.analysis import analyze
    matrix, predictions = fixture_files(tmp_path)
    data=pd.read_csv(matrix)
    distances={'C0':0, 'C1':1, 'C4':2, 'C5':3, 'C6':4}
    data['surface_distance']=data.condition.map(distances)
    data.to_csv(matrix,index=False)
    for model in ['LR','RF','ModernBERT']:
        file=predictions/f'{model}_predictions.csv'
        p=pd.read_csv(file)
        p['probability']=.1+p.condition.map(distances)*(.1 if model=='LR' else .05)
        p.to_csv(file,index=False)
    analyze(matrix,predictions,tmp_path/'out',bootstrap_replicates=30)
    secondary=pd.read_csv(tmp_path/'out/statistics/secondary_tests.csv')
    assert len(secondary)==24
    assert set(secondary.true_label)=={0,1}
    assert secondary.loc[(secondary.model=='LR-RF') & (secondary.condition=='C1'),'effect_size'].tolist()==pytest.approx([.05,.05])
    slopes=pd.read_csv(tmp_path/'out/statistics/distance_associations.csv')
    assert len(slopes)==6
    assert set(slopes.N_frames)=={2}
    assert slopes.loc[slopes.model=='LR','effect_size'].tolist()==pytest.approx([.1,.1])
    assert set(pd.read_csv(tmp_path/'out/statistics/primary_tests.csv').confirmatory_or_exploratory)=={'exploratory'}
    wide=pd.read_csv(tmp_path/'out/tables/condition_performance.csv')
    assert len(wide)==5
    assert {'LR_recall','RF_false_positive_rate','ModernBERT_accuracy'} <= set(wide.columns)
    assert {'LR_mean_absolute_delta','RF_mean_absolute_delta','ModernBERT_mean_absolute_delta','N_phishing','N_legitimate'} <= set(wide.columns)
    effects=pd.read_csv(tmp_path/'out/statistics/model_condition_effects.csv')
    assert len(effects)==24 and set(effects.true_label)=={0,1}
    intervals=pd.read_csv(tmp_path/'out/statistics/bootstrap_intervals.csv')
    probability=intervals[intervals.analysis_id.isin(['mean_signed_probability_delta','mean_absolute_probability_delta'])]
    assert len(probability)==48
    assert probability.groupby(['model','condition','true_label']).size().eq(2).all()


def test_empty_primary_cohort_keeps_transition_schema(tmp_path):
    from src.benchmark_v3_2.analysis import analyze
    matrix,predictions=fixture_files(tmp_path)
    data=pd.read_csv(matrix)
    data['primary_complete_case']=False
    data.to_csv(matrix,index=False)
    status=analyze(matrix,predictions,tmp_path/'out',bootstrap_replicates=5)
    assert status['status']=='NOT_RUN_PRIMARY_NO_COMPLETE_CASES_AVAILABLE_PAIRS_AVAILABLE'
    transitions=pd.read_csv(tmp_path/'out/tables/false_positive_transitions.csv')
    assert len(transitions)==12 and transitions.N_frames.eq(0).all()
    assert transitions.new_false_positives.eq(0).all()
    primary=pd.read_csv(tmp_path/'out/statistics/primary_tests.csv')
    assert primary.raw_p.isna().all()
    secondary=pd.read_csv(tmp_path/'out/statistics/available_pair_probability_effects.csv')
    assert len(secondary)==24 and secondary.N_frames.gt(0).all()
    assert set(secondary.true_label)=={0,1}
    assert secondary.mean_absolute_delta.notna().all()
    slopes=pd.read_csv(tmp_path/'out/statistics/available_pair_distance_associations.csv')
    assert len(slopes)==6
    fp=pd.read_csv(tmp_path/'out/tables/available_pair_false_positive_transitions.csv')
    assert len(fp)==12 and fp.new_false_positives.eq(3).all()
