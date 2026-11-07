from ._csv import records, row


def read(path):
    return [row(i, r['Message'], r['Label'], raw_time=r.get('Date', ''), timestamp_quality='mixed_source_unverified')
            for i, r in enumerate(records(path, ['Message', 'Label']), 1)]
