import importlib
import json
import pytest


def source(name):
    return importlib.import_module('src.benchmark_v3.sources.' + name)


def test_mendeley_parser_keeps_raw_labels(tmp_path):
    p = tmp_path / 'x.csv'; p.write_text('LABEL,TEXT\nham,Your card was credited\nspam,Win now\n')
    rows = source('mendeley').read(p)
    assert [r['raw_label'] for r in rows] == ['ham', 'spam']
    assert rows[0]['source_row_id'] == '1'


def test_uci_parser_preserves_tabs_inside_message(tmp_path):
    p = tmp_path / 'x'; p.write_text('ham\tBank\tcredited\nspam\tPrize\n')
    assert source('uci').read(p)[0]['text'] == 'Bank\tcredited'


def test_gateway_has_distinct_six_and_seven_column_schema(tmp_path):
    p = tmp_path / 'x.csv'; p.write_text('messageID,objectID,destination number,message,X,time,error in time\n7,id,+10000000000,Quoted SMS,sender,123,0\n')
    row = source('gateway').read(p)[0]
    assert row['source_row_id'] == '7' and row['text'] == 'Quoted SMS'
    assert row['raw_label'] == 'VT_APWG_flagged'


def test_nus_not_automatically_ham_and_no_collection_date_as_message_time(tmp_path):
    p = tmp_path / 'x.json'
    p.write_text(json.dumps({'smsCorpus': {'message': [{'@id': 9, 'text': {'$': 'Bank notice'}, 'collectionMethod': {'@time': '2015-01-01'}}]}}))
    r = source('nus').read(p)[0]
    assert r['raw_label'] == 'unlabeled' and r['message_timestamp'] == ''


@pytest.mark.parametrize('module,header,line,text,label', [
    ('super_sms', 'SMSes,Labels', 'Example,1', 'Example', '1'),
    ('spam_hunter', 'Messages', 'Example', 'Example', 'spam'),
    ('exais', 'SMS,Label,Message', 'SMS,SPAM,Example', 'Example', 'SPAM'),
    ('smishtank', 'messageid,MainText,Phishing', '3,Example,1', 'Example', 'URL_Phishing=1')])
def test_held_source_parsers_keep_schema_evidence(tmp_path, module, header, line, text, label):
    p = tmp_path / 'x.csv'; p.write_text(header+'\n'+line+'\n')
    r = source(module).read(p)[0]
    assert r['text'] == text and r['raw_label'] == label


def test_harmonization_and_defanging():
    from src.benchmark_v3.core import label_candidate, safe_text, financial_candidate
    assert label_candidate('spam') == 'uncertain'
    assert label_candidate('ham') == 'uncertain'
    assert label_candidate('Smishing') == 'phishing'
    assert financial_candidate('TSB: Your security code is 123456.')
    text = safe_text('Paid $53 on 2022-02-06. Visit https://bad.example/2022-02-06')
    assert '$53' in text and '2022-02-06' in text and 'https' not in text


def test_exact_dedup_preserves_all_origins():
    from src.benchmark_v3.core import exact_dedup
    a = {'id': 'a', 'text': 'Bank credited 50', 'source_id': 'A'}
    b = {'id': 'b', 'text': ' bank  CREDITED 50 ', 'source_id': 'B'}
    unique, duplicates = exact_dedup([a, b])
    assert len(unique) == 1 and len(duplicates) == 1
    assert {r['source_id'] for r in json.loads(unique[0]['origins_json'])} == {'A', 'B'}


def test_unlicensed_duplicate_cannot_displace_licensed_representative():
    from src.benchmark_v3.core import exact_dedup
    rows = [{'id':'a', 'text':'Bank credited 50', 'source_id':'A', 'modeling_allowed':False},
            {'id':'b', 'text':'Bank credited 50', 'source_id':'B', 'modeling_allowed':True}]
    unique, _ = exact_dedup(rows)
    assert unique[0]['id'] == 'b'


def test_family_split_and_holdout_are_isolated():
    from src.benchmark_v3.core import split_families, leakage_errors
    rows = [dict(id=str(i), template_family_id='F'+str(i//2), label=i%2, source_id='B' if i>=16 else 'A') for i in range(20)]
    split = split_families(rows, seed=42, held_out_source='B')
    assert not leakage_errors(split)
    assert all(r['split']=='source_test' for r in split if r['source_id']=='B')
    assert all(r['source_id']!='B' for r in split if r['split']=='train')


def test_temporal_split_rejects_unknown_or_reversed_time():
    from src.benchmark_v3.core import temporal_split
    rows = [dict(id='a', message_timestamp='2020-01-01T00:00:00Z'), dict(id='b', message_timestamp='2022-01-01T00:00:00Z')]
    assert [r['split'] for r in temporal_split(rows, '2021-01-01T00:00:00Z')] == ['train','temporal_test']
    with pytest.raises(ValueError): temporal_split([{'message_timestamp': ''}], '2021-01-01T00:00:00Z')


def test_generator_cannot_receive_scores_and_frozen_hash_checked(tmp_path):
    from src.benchmark_v3.core import assert_blind, verify_hash
    with pytest.raises(ValueError): assert_blind({'nested': {'lr_probability': .3}})
    p = tmp_path/'x'; p.write_text('changed')
    with pytest.raises(ValueError): verify_hash(p, '0'*64)


def test_git_checkout_eol_conversion_is_distinguished_from_content_changes():
    from src.benchmark_v3.ingest import verify_git_blob
    import hashlib
    raw = b'first\nsecond\n'
    expected = hashlib.sha1(f'blob {len(raw)}\0'.encode()+raw).hexdigest()
    assert verify_git_blob(raw.replace(b'\n', b'\r\n'), expected) == 'git_checkout_CRLF_only'
    with pytest.raises(ValueError): verify_git_blob(b'changed\n', expected)


def test_held_legacy_csv_undefined_cp1252_byte_is_preserved_and_flagged(tmp_path):
    from src.benchmark_v3.sources._csv import records
    p = tmp_path/'x.csv'; p.write_bytes(b'Messages\nexample\x81\n')
    row = records(p, ['Messages'])[0]
    assert row['Messages'] == 'example\x81'
    assert row['_source_encoding'] == 'latin-1-byte-preserving-fallback'
