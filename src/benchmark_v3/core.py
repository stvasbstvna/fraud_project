import hashlib
import json
import unicodedata
from datetime import datetime
from pathlib import Path
from collections import defaultdict
from src.benchmark_v2_2.controls import defang, assert_blind
from src.benchmark_v2_2.run import financial_candidate
from src.benchmark_v2_2.source_audit import save_csv, save_json, save_bytes

ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT/'data/benchmark_v3'
RESULTS = ROOT/'results/benchmark_v3'
MODELS = ROOT/'models/benchmark_v3'
CONFIG = ROOT/'configs/benchmark_v3'


def read_json(path):
    return json.loads(Path(path).read_text(encoding='utf-8'))


def digest(value):
    return hashlib.sha256(value if isinstance(value, bytes) else str(value).encode('utf-8')).hexdigest()


def normalize(text):
    return ' '.join(unicodedata.normalize('NFKC', str(text)).casefold().split())


def safe_text(text):
    return defang(text)[0]


def label_candidate(raw):
    return 'phishing' if str(raw).strip().casefold() in {'phishing', 'smishing'} else 'uncertain'


def exact_dedup(rows):
    groups = defaultdict(list)
    for row in rows:
        groups[digest(normalize(row['text']))].append(row)
    unique = []; duplicates = []
    for key, members in sorted(groups.items()):
        members = sorted(members, key=lambda r: (not r.get('modeling_allowed', True), r['source_id'], r['id']))
        origins = [{k: r[k] for k in ('source_id', 'id')} for r in members]
        representative = dict(members[0])
        representative.update(original_normalized_sha256=key, normalized_text=normalize(safe_text(representative['text'])),
                              normalized_sha256=digest(normalize(safe_text(representative['text']))),
                              origins_json=json.dumps(origins, sort_keys=True), duplicate_count=len(members)-1)
        unique.append(representative)
        for row in members[1:]:
            duplicates.append({'representative_id': representative['id'], 'duplicate_id': row['id'],
                               'source_id': row['source_id'], 'original_normalized_sha256': key})
    return unique, duplicates


def split_families(rows, seed=42, held_out_source=None):
    groups = defaultdict(list)
    for row in rows: groups[row['template_family_id']].append(row)
    output = []
    for family, members in sorted(groups.items()):
        if held_out_source and any(r['source_id'] == held_out_source for r in members):
            split = 'source_test'
        else:
            value = int(digest(f'{seed}:{family}')[:16], 16) / 16**16
            split = 'train' if value < .70 else 'validation' if value < .85 else 'held_out_test'
        output.extend(dict(r, split=split) for r in members)
    return output


def leakage_errors(rows):
    errors = []; families = defaultdict(set); texts = defaultdict(set)
    for r in rows:
        families[r['template_family_id']].add(r['split'])
        if r.get('original_normalized_sha256'): texts[r['original_normalized_sha256']].add(r['split'])
        if r['split'] == 'train' and r.get('condition', 'C0') != 'C0': errors.append('rewrite_in_training')
    if any(len(x)>1 for x in families.values()): errors.append('template_cross_split')
    if any(len(x)>1 for x in texts.values()): errors.append('exact_cross_split')
    return sorted(set(errors))


def temporal_split(rows, cutoff):
    boundary = datetime.fromisoformat(cutoff.replace('Z', '+00:00'))
    output = []
    for r in rows:
        stamp = datetime.fromisoformat(r.get('message_timestamp', '').replace('Z', '+00:00'))
        if stamp.tzinfo is None or boundary.tzinfo is None: raise ValueError('Reliable timezone-aware message timestamps required')
        output.append(dict(r, split='train' if stamp < boundary else 'temporal_test'))
    return output


def verify_hash(path, expected):
    if file_digest(path) != expected: raise ValueError('Frozen artifact hash mismatch')


def file_digest(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream,'sha256').hexdigest()
