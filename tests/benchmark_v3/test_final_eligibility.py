from src.benchmark_v3.final_eligibility import acceptable, decide


def annotation(**changes):
    return dict(id='x',english=True,financial_context=True,personal_or_telco=False,valid_legitimate_control=True,confidence=.9,reason='clear financial notice') | changes


def test_english_financial_and_nonpersonal_required():
    good=annotation()
    for field,value in [('english',False),('financial_context',False),('personal_or_telco',True)]:
        bad={**good,field:value}
        assert not acceptable(bad,'phishing')
        assert not decide(bad,bad,None,'phishing')['retained']


def test_controls_cannot_pass_by_financial_keyword_alone():
    bad=annotation(valid_legitimate_control=False)
    assert not acceptable(bad,'legitimate')
    assert acceptable(bad,'phishing')
    assert not decide(annotation(),bad,None,'legitimate')['retained']
