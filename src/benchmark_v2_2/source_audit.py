"""Source capacity and template screening. Candidate counts are not approvals."""
from collections import Counter, defaultdict
import csv
import hashlib
import io
import json
from pathlib import Path

from src.benchmark_v2_1.pilot_templates import template_text, pair_similarity

ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / 'data/benchmark_v2_2'
RESULTS = ROOT / 'results/benchmark_v2_2'


def sha(data):
    return hashlib.sha256(data).hexdigest()


def save_bytes(path, data):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        if path.read_bytes() != data:
            raise FileExistsError(f'Immutable v2.2 output differs: {path}')
        return
    with path.open('xb') as handle:
        handle.write(data)


def save_json(path, value):
    save_bytes(path, (json.dumps(value, indent=2, ensure_ascii=False, sort_keys=True) + '\n').encode())


def save_csv(path, rows, fields=None):
    if fields is None:
        fields = list(dict.fromkeys(k for row in rows for k in row))
    stream = io.StringIO(newline='')
    writer = csv.DictWriter(stream, fieldnames=fields, lineterminator='\n')
    writer.writeheader(); writer.writerows(rows)
    save_bytes(path, stream.getvalue().encode('utf-8'))


def map_label(label):
    return {'ham': 'legitimate', 'legitimate': 'legitimate', 'smishing': 'phishing_scam',
            'phishing': 'phishing_scam', 'phishing_scam': 'phishing_scam',
            'scam': 'scam_requires_phishing_review'}.get(str(label).strip().casefold(), 'unknown')


def screen_families(rows, references):
    """Same numerical v2.1 thresholds; connected components and overlap propagation.

    Inverted token counts skip pairs whose Jaccard cannot reach 0.45. All
    potentially matching pairs still receive the exact structural comparison.
    References participate in components, so reference bridges also quarantine.
    """
    records = [{'text': r['safe_text'], 'entity': r.get('institution_entity', ''), 'kind': '', 'id': r['frame_id']} for r in rows]
    records += [{'text': r['text'], 'entity': r.get('entity', ''), 'kind': r['kind'], 'id': r['id']} for r in references]
    entities = sorted({r.get('institution_entity', '') for r in rows} - {'', 'NONE'}, key=lambda x: (-len(x), x))
    normalized = [template_text(r['text'], r.get('entity') or next((e for e in entities if e.casefold() in r['text'].casefold()), '')) for r in records]
    parents = list(range(len(records)))
    def root(i):
        while parents[i] != i:
            parents[i] = parents[parents[i]]; i = parents[i]
        return i
    inverted = defaultdict(list); tokens = []; identical = {}
    for i, text in enumerate(normalized):
        words = set(text.split()); intersections = Counter()
        if text in identical:
            a, b = root(i), root(identical[text]); parents[max(a, b)] = min(a, b)
            tokens.append(words)
            continue
        identical[text] = i
        for word in words:
            intersections.update(inverted[word])
        for j, intersection in intersections.items():
            union = len(words) + len(tokens[j]) - intersection
            if union and intersection / union >= .45 and pair_similarity(text, normalized[j])[2]:
                a, b = root(i), root(j); parents[max(a, b)] = min(a, b)
        tokens.append(words)
        for word in words: inverted[word].append(i)
    groups = defaultdict(list)
    for i in range(len(records)): groups[root(i)].append(i)
    for i, row in enumerate(rows):
        members = groups[root(i)]
        witnesses = sorted((records[j]['kind'], records[j]['id']) for j in members if records[j]['kind'])
        # Prefer a concrete training witness when both prior and training match.
        witnesses.sort(key=lambda x: (x[0] != 'train_validation', x))
        row.update(template_family_id='V22-TF-' + sha('\n'.join(sorted({normalized[j] for j in members})).encode())[:20],
                   overlap_kind=witnesses[0][0] if witnesses else '',
                   overlap_reference=witnesses[0][1] if witnesses else '')
    return rows


def capacity_bound(rows):
    usable = [r for r in rows if not r['rule_errors']]
    real = {r['template_family_id'] for r in usable if r['candidate_label'] == 'legitimate' and r['real_vs_synthetic'] == 'real'}
    synthetic = {r['template_family_id'] for r in usable if r['candidate_label'] == 'legitimate' and r['real_vs_synthetic'] == 'synthetic'} - real
    # Deliberately optimistic: ignore class/source competition and assume every
    # remaining ham candidate passes semantic review. It is an upper bound only.
    controls = len(real) + min(len(synthetic), len(real) // 3)
    control_rows = [r for r in usable if r['candidate_label'] == 'legitimate']
    lineage_counts = {}
    if control_rows and all(r.get('source_group') for r in control_rows):
        groups = defaultdict(set)
        for r in control_rows:
            groups[r['source_group']].add(r['template_family_id'])
        lineage_counts = {key: len(values) for key, values in sorted(groups.items())}
        # Overlapping families across groups are counted multiple times here:
        # this remains an optimistic bound, never a claim that such a cohort
        # can actually be selected. No group may exceed half of a class.
        controls = min(controls, 2 * (sum(lineage_counts.values()) - max(lineage_counts.values())))
    positives = {r['template_family_id'] or 'UNSCREENED-ROW-' + r['frame_id'] for r in usable if r['candidate_label'] in {'phishing_scam', 'scam_requires_phishing_review'}}
    return {'real_legitimate_candidate_families': len(real), 'synthetic_legitimate_candidate_families': len(synthetic),
            'maximum_legitimate_before_semantic_review': controls,
            'legitimate_candidate_family_capacity_by_lineage': lineage_counts,
            'phishing_candidate_capacity_upper_bound': len(positives),
            'source_capacity_sufficient': controls >= 16 and len(positives) >= 16,
            'interpretation': 'Optimistic upper bound, not reviewed or frozen source N; semantic review can only reduce this bound.'}
