import csv


def records(path, required):
    for encoding in ('utf-8-sig', 'cp1252', 'latin-1'):
        try:
            with path.open(encoding=encoding, newline='') as handle:
                reader = csv.DictReader(handle)
                if not set(required).issubset(reader.fieldnames or []):
                    raise ValueError(f'Unexpected {path.name} schema: {reader.fieldnames}')
                rows = list(reader)
                for item in rows:
                    item['_source_encoding'] = 'latin-1-byte-preserving-fallback' if encoding == 'latin-1' else encoding
                return rows
        except UnicodeDecodeError:
            continue
    raise ValueError('Unsupported source encoding')


def row(number, text, label, **extra):
    return {'source_row_id': str(number), 'text': str(text), 'raw_label': str(label), 'message_timestamp': '', **extra}
