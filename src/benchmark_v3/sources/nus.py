import json
from ._csv import row


def read(path):
    messages = json.loads(path.read_text(encoding='utf-8-sig'))['smsCorpus']['message']
    return [row(r['@id'], r['text']['$'], 'unlabeled', source_language=r.get('messageProfile', {}).get('@language', 'en_collection'),
                timestamp_quality='collection_time_not_message_time') for r in messages]
