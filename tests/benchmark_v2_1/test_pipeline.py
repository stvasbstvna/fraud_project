import copy
from pathlib import Path

import pandas as pd
import pytest


def api():
    from src.benchmark_v2_1 import core
    return core


def frame():
    return dict(frame_id='F1', source_id='S', source_row_id='1', source_dataset='fixture',
                source_url='', channel='sms', language='en', true_label='phishing_scam',
                banking_related='yes', original_text='Fiction Bank: Review [SAFE-LINK].',
                defanged_text='Fiction Bank: Review [SAFE-LINK].', entity='Fiction Bank',
                requested_action='review the notice', intent='fixture reviewed intent',
                destination='[SAFE-LINK]', contains_url='no', provenance_status='verified',
                license_status='verified', review_status='approved', notes='test fixture')


def matrix():
    c = api(); f = frame(); rows = c.build_matrix(pd.DataFrame([f]))
    for row in rows:
        row.update(generation_status='completed' if row['condition'] != 'C0' else 'not_applicable',
                   variant_text=f['defanged_text'] if row['condition'] == 'C0' else 'Fiction Bank: Please review [SAFE-LINK].',
                   generator_provider='fixture' if row['condition'] != 'C0' else '',
                   generator_model='fixture-v1' if row['condition'] != 'C0' else '',
                   prompt_version='fixture-v1' if row['condition'] != 'C0' else '',
                   generation_attempt=1 if row['condition'] != 'C0' else 0)
    return rows


def reviews(rows):
    c = api()
    return [dict(variant_id=r['variant_id'], text_sha256=c.digest(r['variant_text']),
                 reviewer=who, decision='approved', review_notes='fixture',
                 **{field:'yes' for field in c.REVIEW_FIELDS}) for r in rows for who in ['A','B']]


def test_source_ids_ignore_order_and_duplicate_rows():
    c = api(); rows = pd.DataFrame([frame(), {**frame(), 'source_row_id':'2'}])
    first, dup = c.canonical_frames(rows)
    second, _ = c.canonical_frames(rows.iloc[::-1])
    assert len(first) == 1 and len(dup) == 1
    assert first.frame_id.tolist() == second.frame_id.tolist()


@pytest.mark.parametrize('text', ['https://bad.example/x', 'www.bad.example', 'bad.example/path',
                                      'person@example.com', '+1 (555) 123-4567', 'tel:5551234567',
                                      '192.0.2.1', 'hxxps://bad[.]example', 'ftp://bad.example'])
def test_operational_endpoints_blocked(text):
    assert api().unsafe(text)


def test_defanging_and_safe_placeholders():
    c = api(); text = c.defang('See https://bad.example/x or a@b.com and +1 555 123 4567')
    assert not c.unsafe(text)
    assert '[SAFE-URL-1]' in text and '[SAFE-EMAIL-1]' in text and '[SAFE-PHONE-1]' in text
    assert not c.unsafe('[DEFANGED-ALERT-LINK] [OFFICIAL-APP] $124.00')


def test_dry_run_payload_is_allowlisted():
    c = api(); r = matrix()[1]; r.update(lr_probability=.9, rf_prediction=1, feature_importance='secret')
    payload = c.generation_payload(r)
    assert 'lr_probability' not in payload and 'secret' not in payload and 'rf_prediction' not in payload


def test_pending_frames_cannot_generate():
    c = api(); f=frame(); f['review_status']='pending'
    assert not c.source_eligible(f)
    f=frame(); f['true_label']='spam'
    assert not c.source_eligible(f)
    assert c.source_eligible(frame())


def test_variant_schema_and_placeholders_are_checked():
    c=api(); row=matrix()[1]
    assert c.validate_variant(row) == []
    row['variant_text']='Fiction Bank: please review details.'
    assert 'placeholder_changed' in c.validate_variant(row)
    row['variant_text']='Other Bank: please review [SAFE-LINK].'
    assert 'entity_missing' in c.validate_variant(row)
    row['variant_text']='Fiction Bank: Please review [SAFE-LINK] [NEW-LINK].'
    assert 'placeholder_changed' in c.validate_variant(row)


def test_freeze_requires_independent_content_bound_complete_reviews():
    c=api(); rows=matrix(); rv=reviews(rows)
    assert c.freeze_rows(rows,rv)
    with pytest.raises(ValueError): c.freeze_rows(rows,rv[:1])
    changed=copy.deepcopy(rows); changed[1]['variant_text'] += ' Changed.'
    with pytest.raises(ValueError): c.freeze_rows(changed,rv)
    rv[0]['action_preserved']='no'
    with pytest.raises(ValueError): c.freeze_rows(rows,rv)


def test_identical_reviewers_do_not_count_twice():
    c=api(); rows=matrix(); rv=reviews(rows)
    for r in rv:r['reviewer']='A'
    with pytest.raises(ValueError):c.freeze_rows(rows,rv)


@pytest.mark.parametrize('mutation', ['missing','duplicate','label','action','c0','entity','destination'])
def test_freeze_rejects_invariant_and_matrix_errors(mutation):
    c=api(); rows=matrix(); rv=reviews(rows)
    if mutation=='missing':rows.pop()
    elif mutation=='duplicate':rows[-1]['condition']='C5'
    elif mutation=='label':rows[1]['true_label']='legitimate'
    elif mutation=='action':rows[1]['requested_action']='new action'
    elif mutation=='c0':rows[0]['variant_text']='Changed anchor'
    elif mutation=='entity':rows[1]['entity']='New Bank'
    elif mutation=='destination':rows[1]['destination']='[OTHER]'
    with pytest.raises(ValueError):c.freeze_rows(rows,rv)


def test_evaluation_validation_rejects_invalid_probabilities():
    c=api(); rows=matrix()
    for r in rows:r.update(lr_probability=.8,rf_probability=.7,lr_prediction=1,rf_prediction=1)
    c.validate_predictions(pd.DataFrame(rows))
    for val in [-.1,1.1,float('nan'),float('inf')]:
        bad=copy.deepcopy(rows);bad[1]['lr_probability']=val
        with pytest.raises(ValueError):c.validate_predictions(pd.DataFrame(bad))


def test_outputs_cannot_overwrite_old_artifacts(tmp_path):
    c=api()
    with pytest.raises(ValueError):c.write_csv(Path('data/final/dataset_summary.csv'),[],['test'])
    output=tmp_path/'new.csv';c.write_csv(output,[{'x':1}],['x'],root=tmp_path)
    with pytest.raises(FileExistsError):c.write_csv(output,[{'x':2}],['x'],root=tmp_path)


def test_frame_cluster_bootstrap_and_degenerate_inference():
    from src.benchmark_v2_1.statistics import mean_ci, one_sample, holm
    assert mean_ci([0,0,0],seed=42)==(0.,0.)
    assert one_sample([0,0,0])['p_value']==1.
    assert one_sample([1])['status']=='insufficient_frames'
    assert holm([.01,.04,.2])==pytest.approx([.03,.08,.2])
