from ._csv import records, row


def read(path):
    return [row(i, r['SMSes'], r['Labels']) for i, r in enumerate(records(path, ['SMSes', 'Labels']), 1)]
