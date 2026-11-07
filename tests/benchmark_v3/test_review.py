import pytest


def test_review_requires_financial_semantics_and_high_confidence():
    from src.benchmark_v3.semantic_review import acceptable, decide
    good = {'id':'x','label':'legitimate','financial':True,'safe':True,'message_function':'transaction','confidence':.95,'reason':'Bank alert'}
    assert acceptable(good)
    assert not acceptable(good | {'financial': False})
    assert not acceptable(good | {'confidence': .79})
    assert decide(good, good)['approved']
    assert not decide(good, good | {'label':'uncertain'})['approved']


def test_batch_ids_must_be_exact_not_fabricated_or_missing():
    from src.benchmark_v3.semantic_review import validate_ids
    validate_ids([{'id':'a'}], {'items':[{'id':'a'}]})
    with pytest.raises(ValueError): validate_ids([{'id':'a'}], {'items':[{'id':'b'}]})


def test_nonoperational_phishing_is_not_confused_with_benign_message():
    from src.benchmark_v3.semantic_review import acceptable, decide
    x={'id':'x','label':'phishing','financial':True,'nonoperational_text':True,'message_function':'account_restriction','confidence':.95,'reason':'Defanged bank impersonation'}
    assert acceptable(x, version='v3.1')
    assert decide(x,x,version='v3.1')['approved']
    assert not acceptable(x | {'nonoperational_text':False}, version='v3.1')
