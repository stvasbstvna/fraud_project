import importlib


def api():
    return importlib.import_module('src.benchmark_v2_2.source_review')


def assessment(**changes):
    row = dict(decision='approve', validated_label='legitimate', banking_related=True, bank_origin_notification=True,
               institution_entity='MetroTrust', requested_action='NONE', destination_type='none', destination_value_safe='NONE',
               message_function='transaction_alert', intent='inform a transaction', product_or_service='card',
               event_or_claim='transaction completed', amount='53', date_or_time='NONE', safe=True, confidence=.95, reason='Clear bank notification')
    return row | changes


def test_non_action_bank_notification_can_pass_source_review():
    assert api().good(assessment())
    assert not api().good(assessment(bank_origin_notification=False))
    assert not api().good(assessment(confidence=.79))


def test_casual_bank_reference_cannot_become_notification_control():
    result = assessment(decision='reject', banking_related=False, bank_origin_notification=False, validated_label='not_banking')
    assert not api().good(result)


def test_consensus_requires_agreement_on_typed_semantics():
    assert api().consensus(assessment(), assessment()) == 'approve'
    assert api().consensus(assessment(), assessment(institution_entity='OtherBank')) == 'adjudicate'
    assert api().consensus(assessment(decision='reject'), assessment(decision='reject')) == 'reject'
