from ._csv import records, row


def read(path):
    return [row(r['messageid'], r['MainText'], 'URL_Phishing='+r['Phishing'], raw_time=r.get('timeReceived', ''), source_encoding=r['_source_encoding'],
                timestamp_quality='source_semantics_unverified') for r in records(path, ['messageid', 'MainText', 'Phishing'])]
