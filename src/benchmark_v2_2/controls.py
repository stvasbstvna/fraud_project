"""Prospective safety and scientific gates, independent of detector outputs."""
from collections import Counter
from difflib import SequenceMatcher
import hashlib
import html
import re

CORE = frozenset({'C0', 'C1', 'C4', 'C5', 'C6'})
QUALITY_REASONS = frozenset({'unchanged', 'malformed', 'placeholder_damage', 'deterministic_semantic_violation'})


def defang(text):
    """Typed span redaction; protect dates, times and money before phone matching.

    Ordinary dates/amounts remain literal. DATE/AMOUNT span types record their
    protected status; account/transaction IDs and operational endpoints redact.
    Ambiguous numeric spans are OTHER-ID, never confidently invented phones.
    """
    text = html.unescape(str(text))
    spans = []
    def collect(pattern, kind, replace=True, flags=re.I, group=0):
        for m in re.finditer(pattern, text, flags):
            a, b = m.span(group)
            if any(a < y and b > x for x, y, *_ in spans):
                continue
            spans.append((a, b, kind, replace))
    collect(r'\[[A-Z][A-Z0-9-]*\]', 'EXISTING', False)
    # Operational endpoints outrank facts embedded inside their paths. Protect
    # ordinary dates/money only after the complete endpoint has been removed.
    collect(r'\b(?:https?|hxxps?)\s*:\s*//[^\s<>]+', 'SAFE-URL')
    collect(r'\b[\w.+-]+@[\w-]+(?:\.|\[\.\])[\w.-]+', 'SAFE-EMAIL')
    collect(r'\b(?:www\.)?(?:[a-z0-9-]+(?:\.|\[\.\]))+[a-z]{2,63}(?:[/:][^\s<>]*)?', 'SAFE-URL')
    collect(r'\b(?:\d{1,3}\.){3}\d{1,3}(?:[/:][^\s<>]*)?', 'SAFE-URL')
    collect(r'\b(?:\d{1,2}[/-]\d{1,2}[/-]\d{2,4}|\d{4}-\d{2}-\d{2})\b', 'DATE', False)
    collect(r'\b\d{1,2}:\d{2}(?::\d{2})?(?:\s*[ap]m)?\b', 'TIME', False)
    collect(r'(?:[$£€₹]|\b(?:AUD|USD|GBP|INR|Rs\.?|BDT|Tk\.?))\s*\d[\d,]*(?:\.\d{1,2})?|\b\d[\d,]*(?:\.\d{1,2})?\s*(?:GBP|USD|AUD|INR|BDT)\b', 'AMOUNT', False)
    collect(r'\b(?:a/c|acct?|account|card)(?:\s*(?:number|no\.?|ending|ending in))?\s*[:#-]?\s*([xX*]*\d[\dxX*-]{3,})', 'ACCOUNT-ID', group=1)
    collect(r'\b(?:ref(?:erence)?|txn|transaction\s*(?:id|no\.?))\s*[:#-]?\s*([A-Z0-9][A-Z0-9-]{5,})', 'TRANSACTION-ID', group=1)
    collect(r'(?<![\w])\+\d[\d ()-]{6,}\d(?![\w])', 'SAFE-PHONE')
    collect(r'\b(?:call|phone|tel|telephone|contact)(?:\s+(?:us|on|at))?\s*[:.-]?\s*(\d[\d ()-]{6,}\d)', 'SAFE-PHONE', group=1)
    collect(r'(?<![\w.])\d{7,}(?![\w.])', 'OTHER-ID')
    counts = Counter(); output = []; cursor = 0; records = []
    for a, b, kind, replace in sorted(spans):
        output.append(text[cursor:a]); counts[kind] += 1
        output.append(f'[{kind}-{counts[kind]}]' if replace else text[a:b])
        records.append({'start': a, 'end': b, 'type': kind, 'redacted': replace,
                        'span_sha256': hashlib.sha256(text[a:b].encode()).hexdigest()})
        cursor = b
    output.append(text[cursor:])
    return ''.join(output), records


def valid_institution(entity, text):
    if entity == 'NONE':
        return True
    if not entity or entity not in text or len(entity.split()) > 6:
        return False
    return not re.search(r'\d|\[|\b(?:transaction|payment|credited|debited|your|for|of|completed|available|notification)\b', entity, re.I)


def action_eligibility(text, action):
    if not action or action in {'NONE', 'no_action'}:
        return {'C2': 'no_action', 'C3': 'no_action'}
    if re.search(r'\b(?:click|call|visit|reply|open|log\s?in)\b.{0,90}\b(?:verify|account|here|number|app|link)\b', text, re.I):
        return {'C2': 'already_direct', 'C3': 'semantic_review_required'}
    return {'C2': 'semantic_review_required', 'C3': 'semantic_review_required'}


def core_complete(approved):
    return CORE.issubset(approved)


def c1_errors(original, variant):
    a = re.findall(r'\w+|\[[^]]+\]', original.casefold())
    b = re.findall(r'\w+|\[[^]]+\]', variant.casefold())
    # This is a necessary surface screen; semantic reviewers must also establish
    # that at least two changes are meaningful lexical substitutions.
    substitutions = sum(min(i2-i1, j2-j1) for op, i1, i2, j1, j2 in SequenceMatcher(None, a, b, autojunk=False).get_opcodes() if op == 'replace')
    return ['fewer_than_two_lexical_substitutions'] if substitutions < 2 else []


def source_errors(rows):
    errors = []
    labels = ('phishing_scam', 'legitimate')
    by_label = {label: [r for r in rows if r.get('true_label') == label] for label in labels}
    counts = [len(by_label[x]) for x in labels]
    if min(counts) < 16: errors.append('minimum_16_per_class')
    if counts[0] != counts[1]: errors.append('class_imbalance')
    groups = {label: Counter(r.get('source_group', '') for r in by_label[label]) for label in labels}
    if any(len(g) < 2 or '' in g for g in groups.values()): errors.append('source_diversity')
    if any(g and max(g.values()) > len(by_label[label]) / 2 for label, g in groups.items()): errors.append('source_exceeds_half_class')
    if not (set(groups[labels[0]]) & set(groups[labels[1]])): errors.append('perfect_source_label_confounding')
    controls = by_label['legitimate']
    if controls and sum(r.get('real_vs_synthetic') == 'synthetic' for r in controls) / len(controls) > .25:
        errors.append('synthetic_controls_above_25_percent')
    if any(r.get('real_vs_synthetic') not in {'real', 'synthetic'} for r in controls): errors.append('control_authorship_unresolved')
    if any(r.get('source_review_approved') is not True for r in rows): errors.append('unapproved_source')
    if any(r.get('overlap_clear') is not True for r in rows): errors.append('unresolved_contamination')
    if any(r.get('provenance_approved') is not True for r in rows): errors.append('unapproved_provenance')
    families = [r.get('template_family_id') for r in rows]
    if len(set(families)) != len(rows) or any(not x for x in families): errors.append('template_duplicates_or_missing')
    return errors


def require_scoring(source_manifest, phishing_complete, legitimate_complete, approval_rates):
    if source_manifest.get('status') != 'FROZEN_ACCEPTED_SOURCES' or source_manifest.get('verified') is not True:
        raise ValueError('Accepted verified source freeze required before scoring')
    if min(phishing_complete, legitimate_complete) < 12:
        raise ValueError('At least 12+12 complete core cases required')
    for condition, minimum in {'C1': .75, 'C4': .80, 'C5': .75, 'C6': .70}.items():
        if approval_rates.get(condition, -1) < minimum:
            raise ValueError(f'{condition} approval gate failed')


def assert_blind(payload):
    if isinstance(payload, dict):
        for key, value in payload.items():
            if re.search(r'probability|prediction|detector|threshold_transition|baseline_score|delta_from', key, re.I):
                raise ValueError('detector feedback forbidden')
            assert_blind(value)
    elif isinstance(payload, list):
        for value in payload: assert_blind(value)


def retry_allowed(reason, attempt):
    return attempt == 1 and reason in QUALITY_REASONS
