import importlib


def api():
    return importlib.import_module('src.benchmark_v2_2.source_audit')


def test_upper_bound_synthetic_cap():
    rows = [{'candidate_label': 'legitimate', 'real_vs_synthetic': 'real', 'template_family_id': str(i), 'rule_errors': ''} for i in range(9)]
    rows += [{'candidate_label': 'legitimate', 'real_vs_synthetic': 'synthetic', 'template_family_id': 's'+str(i), 'rule_errors': ''} for i in range(20)]
    result = api().capacity_bound(rows)
    assert result['maximum_legitimate_before_semantic_review'] == 12
    assert result['source_capacity_sufficient'] is False


def test_held_mixed_channels_do_not_count_as_sms_capacity():
    rows = [{'candidate_label': 'legitimate', 'real_vs_synthetic': 'real', 'template_family_id': str(i), 'rule_errors': 'row_channel_unresolved'} for i in range(30)]
    assert api().capacity_bound(rows)['maximum_legitimate_before_semantic_review'] == 0


def test_source_lineage_capacity_cannot_inflate_control_count():
    rows = [{'candidate_label': 'legitimate', 'real_vs_synthetic': 'real', 'template_family_id': str(i), 'rule_errors': '', 'source_group': 'UCI'} for i in range(49)]
    rows += [{'candidate_label': 'legitimate', 'real_vs_synthetic': 'real', 'template_family_id': str(i), 'rule_errors': '', 'source_group': 'MENDELEY'} for i in range(7)]
    assert api().capacity_bound(rows)['maximum_legitimate_before_semantic_review'] == 14


def test_source_label_mapping_does_not_promote_spam():
    assert api().map_label('spam') == 'unknown'
    assert api().map_label('ham') == 'legitimate'
    assert api().map_label('Smishing') == 'phishing_scam'
    assert api().map_label('scam') == 'scam_requires_phishing_review'


def test_exclusive_writer_refuses_changed_output(tmp_path):
    path = tmp_path / 'x.json'
    api().save_json(path, {'a': 1})
    api().save_json(path, {'a': 1})
    import pytest
    with pytest.raises(FileExistsError):
        api().save_json(path, {'a': 2})


def test_family_screen_preserves_v21_threshold_and_propagates_overlap():
    rows = [{'safe_text': 'Bank: Your account was credited with 150 dollars.', 'institution_entity': 'Bank', 'frame_id': 'a'},
            {'safe_text': 'Bank: Your account was credited with 200 dollars.', 'institution_entity': 'Bank', 'frame_id': 'b'}]
    reference = [{'text': rows[0]['safe_text'], 'id': 'training-1', 'kind': 'train_validation'}]
    result = api().screen_families(rows, reference)
    assert result[0]['template_family_id'] == result[1]['template_family_id']
    assert all(r['overlap_kind'] == 'train_validation' for r in result)


def test_real_reference_loader_handles_abstract_v2_frames():
    from src.benchmark_v2_2.run import references
    reference, ledger = references()
    assert len(reference) > 1000
    assert all(r['text'] for r in reference)
    assert any('benchmark_v2/pilot' in r['path'] for r in ledger)


def test_institution_only_verification_message_is_not_lost():
    from src.benchmark_v2_2.run import financial_candidate
    assert financial_candidate('TSB: Your security code is 123456. Never share this code.')
