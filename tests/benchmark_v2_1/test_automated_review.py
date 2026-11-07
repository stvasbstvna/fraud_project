import copy
import pandas as pd
import pytest


def assessment(label='legitimate'):
    return dict(banking_related=True,label_assessment=label,intent='inform about an account update',
        requested_action='review in the official app',entity='Example Bank',destination='[OFFICIAL-APP]',
        channel='sms',semantic_confidence=.95,safe=True,reason='test fixture')


def test_machine_source_decision_never_requires_or_fakes_human_approval():
    from src.benchmark_v2_1.automated_review import source_decision
    a=assessment();r=source_decision(a,copy.deepcopy(a))
    assert r['review_mode']=='automated' and r['approved']
    assert 'human_approved' not in r
    assert not source_decision({**a,'semantic_confidence':.79},a)['approved']


def test_disagreeing_source_assessments_require_actual_adjudication():
    from src.benchmark_v2_1.automated_review import source_decision
    a=assessment();b=assessment('phishing')
    r=source_decision(a,b)
    assert not r['approved'] and r['needs_adjudication']
    assert not source_decision(a,b,{'decision':'uncertain','confidence':.99})['approved']


def test_rewrite_consensus_requires_every_critical_field():
    from src.benchmark_v2_1.automated_review import rewrite_decision,REWRITE_BOOLEANS
    a={**{k:True for k in REWRITE_BOOLEANS},'new_facts':False,'confidence':.95,'reason':'fixture'}
    assert rewrite_decision(a,a)['approved']
    b={**a,'same_action':False}
    assert not rewrite_decision(a,b)['approved']
    assert rewrite_decision(a,b)['needs_adjudication']


def test_automated_rewrite_validation_preserves_all_placeholders_and_numbers():
    from src.benchmark_v2_1.automated_review import rewrite_errors
    r=dict(condition='C1',defanged_text='Example Bank: Payment $20 to [LINK] [0000].',
           variant_text='Example Bank: Your payment $20 is at [LINK] [0000].',entity='Example Bank',destination='[LINK]')
    assert rewrite_errors(r)==[]
    assert 'numeric_fact_changed' in rewrite_errors({**r,'variant_text':r['variant_text'].replace('$20','$30')})
    assert 'placeholder_changed' in rewrite_errors({**r,'variant_text':r['variant_text'].replace('[0000]','')})
    assert 'unsafe_endpoint' in rewrite_errors({**r,'variant_text':r['variant_text']+' bad.example'})


def test_balanced_automated_cohort_can_reduce_n_without_changing_human_gate():
    from src.benchmark_v2_1.automated_sources import balanced_cohort
    rows=[dict(frame_id=str(i),true_label=label,source_id=src,template_family_id=f'F{i}',entity=f'Bank {i}',intent_category='notice')
          for i,(label,src) in enumerate([('phishing_scam','A'),('phishing_scam','A'),('phishing_scam','B'),('legitimate','C'),('legitimate','C')])]
    f=balanced_cohort(pd.DataFrame(rows),target_per_label=24)
    assert len(f)==4 and f.true_label.value_counts().to_dict()=={'phishing_scam':2,'legitimate':2}
    assert f.template_family_id.is_unique and f.source_id.value_counts().max()<=len(f)/2


def test_machine_freeze_rejects_pending_reviews_and_incomplete_conditions():
    from src.benchmark_v2_1.automated_freeze import validate_automated_matrix
    with pytest.raises(ValueError):validate_automated_matrix(pd.DataFrame())
    with pytest.raises(ValueError):validate_automated_matrix(pd.DataFrame([{'frame_id':'x','condition':'C0','review_mode':'human'}]))


def test_api_request_payload_never_includes_detector_data():
    from src.benchmark_v2_1.automated_review import source_payload
    r={'frame_id':'x','safe_text':'safe','source_id':'S','original_dataset':'D','original_url':'internal',
       'license_status':'verified','raw_label':'ham','label_source':'source','lr_probability':.99,'rf_prediction':1}
    p=source_payload(r)
    assert 'lr_probability' not in p and 'rf_prediction' not in p


def test_automated_writer_can_resume_identical_artifacts_but_not_change_them(tmp_path):
    from src.benchmark_v2_1.automated_io import write_csv
    p=tmp_path/'result.csv'
    write_csv(p,[{'x':1}],['x'],root=tmp_path)
    before=p.read_bytes();write_csv(p,[{'x':1}],['x'],root=tmp_path)
    assert p.read_bytes()==before
    with pytest.raises(FileExistsError):write_csv(p,[{'x':2}],['x'],root=tmp_path)
