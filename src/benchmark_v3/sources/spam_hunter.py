from ._csv import records, row


def read(path):
    return [row(i, r['Messages'], 'spam') for i, r in enumerate(records(path, ['Messages']), 1)]
