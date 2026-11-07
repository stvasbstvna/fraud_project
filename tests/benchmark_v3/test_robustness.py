from src.benchmark_v3.robustness import invariant_errors, select_sources, complete_core


def test_placeholder_multiplicity_and_numbers():
    source = 'Bank paid $25.00 [SAFE-URL-1] [SAFE-URL-1]'
    assert 'placeholders' in invariant_errors(source, 'Bank paid $25.00 [SAFE-URL-1]', 'C5', 'Bank')
    assert 'numbers' in invariant_errors(source, 'Bank paid $35.00 [SAFE-URL-1] [SAFE-URL-1]', 'C5', 'Bank')


def test_institution_and_c1_copy():
    assert 'institution' in invariant_errors('Chase account locked', 'Citi account frozen', 'C1', 'Chase')
    assert 'c1_insufficient_lexical_change' in invariant_errors('Chase account locked', 'Chase account locked!', 'C1', 'Chase')


def test_selection_whitelists_and_core():
    rows = [{'id':'a','safe_text':'x','label':'phishing','source_id':'s','template_family_id':'f','split':'held_out_test','prediction':.2}]
    selected = select_sources(rows)
    assert 'prediction' not in selected[0]
    assert complete_core([{'frame_id':'a','condition':c} for c in ['C0','C1','C4','C5','C6']]) == ['a']
    assert complete_core([{'frame_id':'a','condition':'C0'}]) == []
