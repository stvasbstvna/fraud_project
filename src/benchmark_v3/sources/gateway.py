import csv
from ._csv import row


def read(path):
    with path.open(encoding='utf-8-sig', newline='') as handle: data = list(csv.reader(handle))
    headers = [['messageID','objectID','destination number','message','time','error in time'],
               ['messageID','objectID','destination number','message','X','time','error in time']]
    if not data or data[0] not in headers or any(len(r) != 7 for r in data[1:]): raise ValueError('Unexpected Gateway layout')
    return [row(r[0], r[3], 'VT_APWG_flagged', raw_time=r[5], timestamp_quality='source_semantics_unverified') for r in data[1:]]
