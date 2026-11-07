"""Typed semantic decision rules. No model execution when capacity gate fails."""
from .controls import valid_institution

FIELDS = ('validated_label', 'banking_related', 'bank_origin_notification', 'institution_entity',
          'requested_action', 'destination_type', 'destination_value_safe', 'message_function',
          'intent', 'product_or_service', 'event_or_claim', 'amount', 'date_or_time')


def good(review):
    return (review.get('decision') == 'approve' and review.get('validated_label') == 'legitimate'
            and review.get('banking_related') is True and review.get('bank_origin_notification') is True
            and review.get('safe') is True and isinstance(review.get('confidence'), (float, int))
            and .8 <= review['confidence'] <= 1
            and all(isinstance(review.get(key), (str, bool)) for key in FIELDS))


def consensus(a, b):
    if not good(a) and not good(b): return 'reject'
    if good(a) and good(b) and all(a[key] == b[key] for key in FIELDS): return 'approve'
    return 'adjudicate'
