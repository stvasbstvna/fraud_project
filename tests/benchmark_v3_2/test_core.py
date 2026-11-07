import pytest
from src.benchmark_v3_2.core import immutable_json, sha, blind, complete_ids, retry_allowed, approved_source, approved_rewrite

def test_immutable_write_rejects_change(tmp_path):
    p=tmp_path/'x.json'
    immutable_json(p, {'value':1})
    immutable_json(p, {'value':1})
    with pytest.raises(ValueError): immutable_json(p, {'value':2})

def test_blind_checks_nested_scores():
    blind({'text':'message'})
    with pytest.raises(ValueError): blind({'items':[{'RF_probability':.8}]})

def test_complete_rejects_duplicates_and_requires_all():
    rows=[{'frame_id':'a','condition':c} for c in ['C0','C1','C4','C5','C6']]
    assert complete_ids(rows)=={'a'}
    assert complete_ids(rows[:-1])==set()
    with pytest.raises(ValueError): complete_ids(rows+[rows[0]])

def test_quality_retry_only_once_never_score_driven():
    assert retry_allowed(0, ['unchanged'])
    assert not retry_allowed(1,['unchanged'])
    assert not retry_allowed(0,['low_probability'])

def test_source_and_rewrite_require_every_gate():
    a=dict(banking_related=True,label='legitimate',language='English',channel='sms',safe=True,confidence=.9,decision='approve')
    assert approved_source(a)
    assert not approved_source(a|{'language':'Portuguese'})
    r={k:True for k in ['same_intent','same_requested_action','same_institution_entity','same_destination','same_event','same_label','no_new_facts','safe','condition_followed','meaningfully_changed','natural_language']}
    r['confidence']=.9
    assert approved_rewrite(r)
    assert not approved_rewrite(r|{'same_requested_action':False})
