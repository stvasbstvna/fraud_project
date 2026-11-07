import pytest
from src.benchmark_v3_2.sources import validate_packet
from src.benchmark_v3_2.generate import deterministic_errors

def test_source_review_cannot_transfer_between_texts():
    packet=[dict(id='a',frame_id='a',safe_text='Bank notice A',source_dataset='nus',source_row_id='1',original_label='unlabeled',original_url='url')]
    row=dict(id='a',safe_text='Bank notice A',source_id='nus',source_row_id='1',raw_label='unlabeled',source_url='url')
    validate_packet(packet,[row])
    with pytest.raises(ValueError):validate_packet(packet,[row|{'safe_text':'changed'}])
    with pytest.raises(ValueError):validate_packet(packet,[row,row])

def test_technical_failure_does_not_become_quality_retry():
    from src.benchmark_v3_2.core import retry_allowed
    job=dict(source='Bank notice',condition='C1',semantic_controls={'institution_entity':'Bank'})
    assert deterministic_errors(job,None)==['missing_provider_evidence']
    assert not retry_allowed(0,deterministic_errors(job,None))

def test_distance_lookup_uses_keys_and_rejects_stale_or_missing_text():
    from src.benchmark_v3_2.score import align_distances
    rows=[dict(frame_id='a',condition='C0',text='original',text_sha256='hash0'),dict(frame_id='a',condition='C1',text='rewrite',text_sha256='hash1')]
    lookup=align_distances(rows,list(reversed(rows)))
    assert lookup['a','C1']['text']=='rewrite'
    with pytest.raises(ValueError):align_distances(rows,rows[:1])
    with pytest.raises(ValueError):align_distances(rows,[rows[0],rows[1]|{'text':'different'}])

def test_legacy_source_masks_are_immutable_too():
    job=dict(source='Bank: card <#> needs review.',condition='C4',semantic_controls={'institution_entity':'Bank'})
    assert 'placeholders' in deterministic_errors(job,{'text':'Bank: please review your card.'})
