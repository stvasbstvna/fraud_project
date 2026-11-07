"""Canonical schemas, objective safety checks and fail-closed scientific gates."""
from __future__ import annotations

import hashlib
import json
import re
from collections import Counter
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / 'data/benchmark_v2_1'
CONFIG = ROOT / 'configs/benchmark_v2_1'
RESULTS = ROOT / 'results/benchmark_v2_1'
CONDITIONS = tuple(f'C{i}' for i in range(7))
FRAME_FIELDS = ('frame_id source_id source_row_id source_dataset source_url channel language '
                'true_label banking_related original_text defanged_text entity requested_action intent '
                'destination contains_url provenance_status license_status review_status notes').split()
INVARIANTS = ('source_id source_row_id source_dataset true_label channel language original_text '
              'defanged_text entity requested_action intent destination').split()
REVIEW_FIELDS = ('semantic_preserved action_preserved entity_preserved destination_preserved '
                 'label_preserved intent_preserved channel_preserved facts_preserved safety_preserved '
                 'naturalness condition_compliance').split()
VARIANT_FIELDS = list(dict.fromkeys(FRAME_FIELDS + ('variant_id condition variant_text generator_provider '
    'generator_model prompt_version prompt_sha256 request_sha256 response_id generated_at_utc '
    'generation_status generation_attempt semantic_preserved action_preserved entity_preserved '
    'destination_preserved label_preserved human_review_status reviewer review_notes '
    'jaccard_similarity normalized_edit_distance tfidf_cosine_similarity lr_tfidf_cosine_similarity '
    'rf_tfidf_cosine_similarity surface_distance lr_probability lr_prediction rf_probability rf_prediction').split()))
PLACEHOLDER = re.compile(r'\[[A-Z][A-Z0-9_-]*\]')
EMAIL = re.compile(r'\b[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}\b')
URL = re.compile(r'(?:[a-z][a-z0-9+.-]*://|www\.)[^\s<>]+|\b(?:[a-z0-9-]+\.)+[a-z]{2,63}(?:/[^\s<>]*)?', re.I)
PHONE = re.compile(r'(?<![\w$])\+?\d[\d ()-]{6,}\d(?!\w)')
IP = re.compile(r'\b(?:\d{1,3}\.){3}\d{1,3}\b')
SPECIAL = re.compile(r'\b(?:tel|mailto|sms):|\[\.\]|\(dot\)|hxxps?://', re.I)


def digest(text: str) -> str:
    return hashlib.sha256(str(text).encode('utf-8')).hexdigest()


def normalize(text: str) -> str:
    return ' '.join(str(text).casefold().split())


def unsafe(text: str) -> bool:
    """Conservative screen, not a substitute for human safety review."""
    visible = PLACEHOLDER.sub('', str(text))
    return any(p.search(visible) for p in (EMAIL, URL, PHONE, IP, SPECIAL))


def defang(text: str) -> str:
    value = str(text)
    for name, pattern in [('EMAIL', EMAIL), ('URL', URL), ('PHONE', PHONE), ('IP', IP)]:
        seen = {}
        def replacement(match):
            key = match.group()
            if key not in seen: seen[key] = f'[SAFE-{name}-{len(seen)+1}]'
            return seen[key]
        value = pattern.sub(replacement, value)
    if unsafe(value):
        raise ValueError('Unresolved endpoint; manual defanging required')
    return value


def write_csv(path: Path, rows, fields: list[str], *, root: Path | None = None):
    """Exclusive creation; no implicit overwrite or path escape."""
    path = Path(path).resolve()
    roots = [root.resolve()] if root else [DATA / p for p in ('source','generated','review','frozen','evaluation','analysis')] + [RESULTS / p for p in ('tables','figures','diagnostics')]
    if not any(path.is_relative_to(p.resolve()) for p in roots):
        raise ValueError(f'Output outside canonical namespace: {path}')
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('x', encoding='utf-8', newline='') as handle:
        pd.DataFrame(rows, columns=fields).to_csv(handle, index=False, lineterminator='\n')


def write_json(path: Path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('x', encoding='utf-8') as handle:
        json.dump(value, handle, indent=2, allow_nan=False)
        handle.write('\n')


def canonical_frames(frame: pd.DataFrame):
    missing = set(FRAME_FIELDS) - set(frame.columns)
    if missing: raise ValueError(f'Missing source columns: {sorted(missing)}')
    frame = frame.fillna('').copy()
    frame['_normalized'] = frame.defanged_text.map(normalize)
    # Across-source identical messages must not be separate independent frames.
    conflicts = frame.groupby('_normalized').true_label.nunique()
    frame = frame.sort_values(['source_id','source_row_id'], kind='stable')
    duplicates = frame[frame.duplicated('_normalized')].copy()
    frame = frame.drop_duplicates('_normalized').copy()
    frame['frame_id'] = frame._normalized.map(lambda text:'BV21-' + digest(text)[:24])
    for index, row in frame.iterrows():
        if not row.defanged_text or unsafe(row.defanged_text):
            frame.at[index,'review_status'] = 'pending'
        if conflicts[row._normalized] > 1:
            frame.at[index,'review_status'] = 'needs_adjudication'
            frame.at[index,'notes'] += '; conflicting source labels'
    duplicates['duplicate_of_frame_id'] = duplicates._normalized.map(lambda text:'BV21-' + digest(text)[:24])
    return frame[FRAME_FIELDS].reset_index(drop=True), duplicates.drop(columns='_normalized')


def source_eligible(row: dict) -> bool:
    return (all(str(row.get(k,'')) == v for k,v in {
        'channel':'sms','language':'en','banking_related':'yes','provenance_status':'verified',
        'license_status':'verified','review_status':'approved'}.items())
        and row.get('true_label') in {'phishing_scam','legitimate'}
        and all(str(row.get(k,'')).strip() for k in ('entity','requested_action','intent','destination','defanged_text'))
        and not unsafe(row['defanged_text']))


def source_digest(row: dict) -> str:
    fields=[k for k in FRAME_FIELDS if k not in {'review_status','notes'}]
    return digest(json.dumps({k:str(row.get(k,'')) for k in fields},sort_keys=True,ensure_ascii=False))


def verify_source_reviews(frames: list[dict], reviews: list[dict]):
    for frame in frames:
        if not source_eligible(frame):raise ValueError('Canonical source not eligible')
        bound=[r for r in reviews if r.get('frame_id')==frame['frame_id'] and r.get('source_sha256')==source_digest(frame)]
        if len({r.get('reviewer','').strip() for r in bound}-{''})<2:
            raise ValueError('Two content-bound source reviews required')
        if any(r.get('decision')!='approved' or any(str(r.get(k,'')).lower()!='yes' for k in REVIEW_FIELDS) for r in bound):
            raise ValueError('Independent source review unresolved')


def build_matrix(frames: pd.DataFrame) -> list[dict]:
    rows = []
    for f in frames.fillna('').to_dict('records'):
        for condition in CONDITIONS:
            row = dict.fromkeys(VARIANT_FIELDS, '')
            row.update(f, variant_id=f"{f['frame_id']}-{condition}", condition=condition,
                       variant_text=f['defanged_text'] if condition == 'C0' else '',
                       generation_status='not_applicable' if condition == 'C0' else 'not_run',
                       generation_attempt=0, human_review_status='pending')
            rows.append(row)
    return rows


def generation_payload(row: dict) -> dict:
    fields = ('frame_id condition true_label channel language entity requested_action intent destination defanged_text').split()
    return {key: row[key] for key in fields}


def validate_variant(row: dict) -> list[str]:
    errors = []
    text = str(row.get('variant_text',''))
    if row.get('condition') not in CONDITIONS: errors.append('unknown_condition')
    if not text.strip(): errors.append('missing_text')
    if unsafe(text): errors.append('unsafe_endpoint')
    if Counter(PLACEHOLDER.findall(text)) != Counter(PLACEHOLDER.findall(str(row.get('defanged_text','')))):
        errors.append('placeholder_changed')
    if str(row.get('entity','')) not in text: errors.append('entity_missing')
    if str(row.get('destination','')) not in text: errors.append('destination_missing')
    if row.get('condition') == 'C0':
        if text != row.get('defanged_text'): errors.append('c0_changed')
    else:
        if text == row.get('defanged_text'): errors.append('unchanged_rewrite')
        if row.get('generation_status') != 'completed': errors.append('generation_incomplete')
        for key in ('generator_provider','generator_model','prompt_version'):
            if not row.get(key): errors.append('metadata_missing:' + key)
        if int(row.get('generation_attempt') or 0) < 1: errors.append('attempt_missing')
    return errors


def validate_matrix(rows: list[dict]):
    if not rows: raise ValueError('No complete eligible frames')
    data = pd.DataFrame(rows).fillna('')
    if data.variant_id.duplicated().any(): raise ValueError('Duplicate variant IDs')
    for frame_id, group in data.groupby('frame_id'):
        if len(group) != 7 or set(group.condition) != set(CONDITIONS):
            raise ValueError(f'Incomplete or duplicate conditions: {frame_id}')
        if any(group[k].nunique(dropna=False) != 1 for k in INVARIANTS):
            raise ValueError(f'Changed invariant: {frame_id}')
        if not source_eligible(group.iloc[0].to_dict()): raise ValueError('Source not eligible')
        for r in group.to_dict('records'):
            if r['variant_id'] != f"{frame_id}-{r['condition']}": raise ValueError('Variant ID mismatch')
            errors=validate_variant(r)
            if errors: raise ValueError(f"{r['variant_id']}: {errors}")
    anchors=data[data.condition.eq('C0')].defanged_text.map(normalize)
    if anchors.duplicated().any(): raise ValueError('Duplicate source texts')


def freeze_rows(rows: list[dict], reviews: list[dict]) -> list[dict]:
    validate_matrix(rows)
    frozen = []
    for row in rows:
        bound = [r for r in reviews if r.get('variant_id') == row['variant_id']
                 and r.get('text_sha256') == digest(row['variant_text'])]
        if not bound or any(r.get('decision') != 'approved' for r in bound):
            raise ValueError('Pending, rejected or conflicting human review')
        if len({r.get('reviewer','').strip() for r in bound} - {''}) < 2:
            raise ValueError('Two independent reviewers required')
        if any(str(r.get(k,'')).lower() != 'yes' for r in bound for k in REVIEW_FIELDS):
            raise ValueError('Human preservation/compliance checks incomplete')
        frozen.append({**row, **{k:True for k in REVIEW_FIELDS[:5]},
                       'human_review_status':'approved',
                       'reviewer':';'.join(sorted({r['reviewer'] for r in bound})),
                       'review_notes':'; '.join(r.get('review_notes','') for r in bound)})
    return frozen


def validate_predictions(data: pd.DataFrame):
    validate_matrix(data.to_dict('records'))
    for model in ('lr','rf'):
        p=pd.to_numeric(data[f'{model}_probability'], errors='raise')
        if not np.isfinite(p).all() or not p.between(0,1).all(): raise ValueError('Invalid probabilities')
        if not data[f'{model}_prediction'].isin([0,1]).all(): raise ValueError('Invalid predictions')
