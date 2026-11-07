"""Original public inputs, separately versioned caches, no private API credentials."""
import io
import json
import urllib.request
import zipfile
import pandas as pd
from .source_audit import DATA, ROOT, sha, save_bytes, save_json

HEADERS = {'User-Agent': 'Mozilla/5.0', 'Accept': '*/*'}


def fetch(name, url, expected=None, offline=False):
    path = DATA / 'source_snapshots' / name
    if path.exists():
        content = path.read_bytes()
    elif offline:
        raise FileNotFoundError(f'Missing original-source snapshot: {path}')
    else:
        with urllib.request.urlopen(urllib.request.Request(url, headers=HEADERS), timeout=60) as response:
            content = response.read()
        if expected and sha(content) != expected:
            raise ValueError(f'Publisher snapshot mismatch: {name}')
        save_bytes(path, content)
    if expected and sha(content) != expected:
        raise ValueError(f'Cached snapshot mismatch: {name}')
    return content


def original_inputs(offline=False):
    from src.benchmark_v2_1.pilot_sources import parse_gateway
    result = []; metadata = []
    def add(sid, frame, text_col, label_col, url, digest, channel, authorship, license, version, note=''):
        metadata.append({'source_id': sid, 'source_url': url, 'source_sha256': digest, 'input_rows': len(frame),
                         'channel': channel, 'authorship': authorship, 'license': license, 'version': version, 'note': note,
                         'label_counts': frame[label_col].value_counts().to_dict()})
        for ordinal, row in enumerate(frame.to_dict('records'), 1):
            result.append({'source_id': sid, 'source_row_id': str(row.get('row_id', ordinal)), 'text': str(row[text_col]),
                           'raw_label': str(row[label_col]), 'channel': channel, 'real_vs_synthetic': authorship,
                           'license': license, 'source_url': url, 'source_sha256': digest, 'version': version})
    url = 'https://data.mendeley.com/public-files/datasets/f45bkkt8pr/files/edb361de-918d-469f-9106-e84823830665/file_downloaded'
    raw = fetch('mendeley_sms_v1.zip', url, '9bbf3188fdad81495d8e82825648b9b63b53fc86841a3d26c02629990b233cc3', offline)
    content = zipfile.ZipFile(io.BytesIO(raw)).read('Dataset_5971.csv')
    frame = pd.read_csv(io.BytesIO(content), keep_default_na=False)
    add('MENDELEY-SMISH', frame, 'TEXT', 'LABEL', 'https://data.mendeley.com/datasets/f45bkkt8pr/1', sha(raw), 'sms', 'real', 'CC_BY_4_0', '1', 'Internet/OCR collection; ham needs independent banking review; UCI overlap screened.')
    url = 'https://archive.ics.uci.edu/static/public/228/sms+spam+collection.zip'
    raw = fetch('uci_sms.zip', url, '1587ea43e58e82b14ff1f5425c88e17f8496bfcdb67a583dbff9eefaf9963ce3', offline)
    content = zipfile.ZipFile(io.BytesIO(raw)).read('SMSSpamCollection').decode('utf-8')
    frame = pd.DataFrame([line.split('\t', 1) for line in content.splitlines()], columns=['label', 'text'])
    add('UCI-SMS', frame, 'text', 'label', 'https://archive.ics.uci.edu/dataset/228/sms+spam+collection', sha(raw), 'sms', 'real', 'CC_BY_4_0', 'original', 'Ham is not automatically a banking notification; spam excluded from phishing.')
    rev = 'a4f18cedc9909cbf8234eea3c2028080a1e95cd4'
    raw = fetch('gateway_phishing.csv', f'https://raw.githubusercontent.com/wspr-ncsu/sms-phishing/{rev}/phishing_messages.csv', 'd125c394af792faeb2b71b3f7100cad3b4cece02aff78cb4ec1fb9e7db90f230', offline)
    frame = pd.DataFrame(parse_gateway(raw))
    add('SMS-GATEWAY', frame, 'text', 'label', 'https://github.com/wspr-ncsu/sms-phishing', sha(raw), 'sms', 'real', 'MIT_repository', rev, 'VT/APWG flags are candidate labels, not definitive message ground truth; ordinal parsing fixes malformed header.')
    meta_raw = fetch('financial_scams_metadata.json', 'https://data.mendeley.com/public-api/datasets/znsk27yk3h', offline=offline)
    meta = json.loads(meta_raw); file = meta['files'][0]
    if meta['data_licence']['short_name'] != 'CC BY 4.0': raise ValueError('New Mendeley source rights changed')
    raw = fetch('financial_scams_v2.csv', file['content_details']['download_url'], file['content_details']['sha256_hash'], offline)
    frame = pd.read_csv(io.BytesIO(raw), keep_default_na=False)
    add('MENDELEY-FINANCIAL', frame, 'message', 'label', f'https://data.mendeley.com/datasets/znsk27yk3h/{meta["version"]}', sha(raw), 'mixed_unresolved', 'real', 'CC_BY_4_0', str(meta['version']), 'Ahmed and Islam; 523 scam/ham rows; source pools SMS/chat/email without per-row channel. HOLD until row-level SMS evidence exists.')
    local = ROOT / 'data/processed/unified_text_messages.csv'
    full = pd.read_csv(local, keep_default_na=False)
    frame = full[full.source_dataset.eq('SmishX')].copy(); frame['row_id'] = frame.id
    add('SMISHX', frame, 'text', 'label', 'https://github.com/yizhu-joy/SmishX', sha(local.read_bytes()), 'sms', 'real', 'MIT_upstream_pending', '116a8c827741e0572563f678d25ed04306b1e3ff', 'Existing detector training source; upstream rights and all train/validation/prior overlaps must be resolved; local normalized copy, not new independent data.')
    metadata.append({'source_id': 'CROSS-MODEL-EMAIL', 'input_rows': int(len(full)-len(frame)), 'decision': 'excluded_channel_email', 'note': 'Human and generated email, not SMS; no candidate promotion.'})
    synthetic = pd.read_csv(ROOT / 'data/benchmark_v2_1/source/frames.csv', keep_default_na=False)
    add('SYNTH-LEGACY', synthetic, 'defanged_text', 'true_label', 'internal', sha((ROOT / 'data/benchmark_v2_1/source/frames.csv').read_bytes()), 'sms', 'synthetic', 'project_authored', 'historical_reference_only', 'Prior benchmark anchors: overlap quarantine; not new v2.2 observations.')
    return result, metadata
