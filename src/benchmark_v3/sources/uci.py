from ._csv import row


def read(path):
    output = []
    for i, line in enumerate(path.read_text(encoding='utf-8-sig').splitlines(), 1):
        fields = line.split('\t', 1)
        if len(fields) != 2 or fields[0] not in {'ham', 'spam'}: raise ValueError('Unexpected UCI row')
        output.append(row(i, fields[1], fields[0]))
    return output
