import importlib
import pytest


def api():
    return importlib.import_module('src.benchmark_v2_2.controls')


def test_date_time_money_not_phone():
    safe, spans = api().defang('On 06/02/2022 at 12:04:43 your card paid AUD 788.93. Call +44 7700 900123.')
    assert '06/02/2022' in safe and '12:04:43' in safe and 'AUD 788.93' in safe
    assert '[SAFE-PHONE-1]' in safe
    assert [r['type'] for r in spans].count('SAFE-PHONE') == 1


def test_account_transaction_url_email_typed():
    safe, spans = api().defang('A/c XX12345678 ref ABC123456 paid Rs. 150.00. Visit https://example.org/a or hxxp://bank[.]invalid/a; email user@example.org.')
    for tag in ['[ACCOUNT-ID-1]', '[TRANSACTION-ID-1]', '[SAFE-URL-1]', '[SAFE-URL-2]', '[SAFE-EMAIL-1]']:
        assert tag in safe
    assert '150.00' in safe
    assert 'example.org' not in safe and 'bank[.]invalid' not in safe


@pytest.mark.parametrize('endpoint', ['https://bank.example/2026-11-06', 'https://bank.example/12:34', 'bank.museum/path', '192.0.2.1/path'])
def test_endpoints_cannot_escape_redaction_through_protected_facts(endpoint):
    safe, _ = api().defang('Visit ' + endpoint)
    assert safe == 'Visit [SAFE-URL-1]'


def test_entity_precision():
    assert api().valid_institution('MetroTrust', 'MetroTrust: transaction for AUD 788.93')
    assert not api().valid_institution('transaction for AUD 788.93', 'transaction for AUD 788.93')
    assert api().valid_institution('NONE', 'Your transfer was completed.')


def test_action_eligibility():
    assert api().action_eligibility('Click here to verify your account', 'click link')['C2'] == 'already_direct'
    assert api().action_eligibility('Your account was credited.', 'NONE')['C2'] == 'no_action'
    assert api().action_eligibility('You may wish to check details.', 'review details')['C2'] == 'semantic_review_required'


def test_core_ignores_ineligible_secondary_but_requires_every_core():
    approved = {'C0', 'C1', 'C4', 'C5', 'C6'}
    assert api().core_complete(approved)
    assert not api().core_complete(approved - {'C6'})


def test_c1_copy_and_punctuation_rejected():
    assert api().c1_errors('Please check your account now.', 'Please check your account now!')
    assert api().c1_errors('Please check your account now.', 'Please check your account now.')
    assert not api().c1_errors('Please check your account now.', 'Kindly review your account now.')


def rows(groups=('A', 'B', 'C'), synthetic=0):
    return [dict(frame_id=f'{label}-{i}', true_label=label, source_group=groups[i % len(groups)],
                 template_family_id=f'{label}-{i}', real_vs_synthetic='synthetic' if label == 'legitimate' and i < synthetic else 'real',
                 source_review_approved=True, overlap_clear=True, provenance_approved=True)
            for label in ('phishing_scam', 'legitimate') for i in range(16)]


def test_source_gate_accepts_qualified_cohort():
    assert api().source_errors(rows()) == []


def test_source_gate_minimum_and_diversity():
    assert 'minimum_16_per_class' in api().source_errors(rows()[:-1])
    assert 'source_diversity' in api().source_errors(rows(groups=('A',)))


def test_confounded_sources_rejected():
    data = rows()
    for r in data:
        r['source_group'] = r['true_label'] + r['source_group']
    assert 'perfect_source_label_confounding' in api().source_errors(data)


def test_synthetic_limit_and_source_capacity():
    assert 'synthetic_controls_above_25_percent' in api().source_errors(rows(synthetic=5))
    assert 'source_exceeds_half_class' in api().source_errors(rows(groups=('A', 'A', 'B')))


def test_source_approval_and_overlap_not_optional():
    data = rows()
    data[0]['source_review_approved'] = False
    data[1]['overlap_clear'] = False
    assert 'unapproved_source' in api().source_errors(data)
    assert 'unresolved_contamination' in api().source_errors(data)


def test_scoring_requires_source_freeze_and_complete_cases():
    with pytest.raises(ValueError, match='source'):
        api().require_scoring({}, 12, 12, {'C1': .8, 'C4': .8, 'C5': .8, 'C6': .8})
    with pytest.raises(ValueError, match='12'):
        api().require_scoring({'status': 'FROZEN_ACCEPTED_SOURCES', 'verified': True}, 11, 12, {'C1': .8, 'C4': .8, 'C5': .8, 'C6': .8})


def test_detector_feedback_and_score_retry_forbidden():
    with pytest.raises(ValueError, match='detector'):
        api().assert_blind({'source': {'baseline_phishing_probability': .1}})
    assert api().retry_allowed('unchanged', 1)
    assert not api().retry_allowed('unchanged', 2)
    assert not api().retry_allowed('low_phishing_score', 1)
