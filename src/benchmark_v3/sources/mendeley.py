from ._csv import records, row


def read(path):
    return [row(i, r['TEXT'], r['LABEL']) for i, r in enumerate(records(path, ['TEXT', 'LABEL']), 1)]
