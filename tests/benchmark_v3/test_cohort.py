import pytest


def test_explicit_telco_balance_veto_cannot_be_overridden_by_review():
    from src.benchmark_v3.cohort import policy_veto
    assert policy_veto('Your Vodafone prepaid account balance is Rs.100')
    assert not policy_veto('Your Savings account was credited INR100')


def test_stratified_family_partition_has_both_classes_and_no_family_overlap():
    from src.benchmark_v3.cohort import stratified_partition
    rows=[{'id':f'{label}-{i}','label':label,'template_family_id':f'{label}-{i}'} for label in ['phishing','legitimate'] for i in range(5)]
    out=stratified_partition(rows)
    assert all({r['label'] for r in out if r['split']==s}=={'phishing','legitimate'} for s in ['train','validation','held_out_test'])
    with pytest.raises(ValueError): stratified_partition(rows[:5]+[{'id':'l','label':'legitimate','template_family_id':'l'}])


def test_person_slots_and_fact_variables_do_not_create_new_templates():
    from src.benchmark_v3.cohort import structural_text
    assert structural_text('You have registered Sinco as Payee for $53.') == structural_text('You have registered Shijo as Payee for $80.')


def test_provider_request_json_is_utf8_on_windows(tmp_path):
    from src.benchmark_v3.core import read_json
    p=tmp_path/'request.json'; p.write_bytes('{"text":"£53 — payment"}'.encode('utf-8'))
    assert read_json(p)['text']=='£53 — payment'


def test_adjudication_chain_must_bind_exact_prior_assessments():
    from src.benchmark_v3.cohort import validate_adjudication_item
    a={'label':'phishing'};b={'label':'uncertain'}
    validate_adjudication_item({'review_A':a,'review_B':b},a,b)
    with pytest.raises(ValueError):validate_adjudication_item({'review_A':b,'review_B':a},a,b)


def test_prospective_protocol_mutation_refuses_reuse(tmp_path):
    from src.benchmark_v3.protocol import check_protocol_hashes
    from src.benchmark_v3.core import file_digest
    p=tmp_path/'protocol.json';p.write_text('original')
    freeze={'protocol_sha256':file_digest(p)}
    check_protocol_hashes(freeze,{'protocol_sha256':p})
    p.write_text('changed')
    with pytest.raises(ValueError):check_protocol_hashes(freeze,{'protocol_sha256':p})
