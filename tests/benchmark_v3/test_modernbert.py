import pytest
from pathlib import Path

from src.benchmark_v3.modernbert import choose_max_length, select_training_rows, verify_frozen_model


def test_training_selection_never_reads_test_text():
    rows = [dict(safe_text='train', label='phishing', split='train'),
            dict(safe_text='valid', label='legitimate', split='validation'),
            dict(safe_text=None, label=None, split='held_out_test')]
    train, validation = select_training_rows(rows)
    assert train == [('train', 1)]
    assert validation == [('valid', 0)]


def test_length_is_bounded_and_selected_from_training_distribution():
    assert choose_max_length([8, 20, 90]) == 128
    assert choose_max_length([129, 200]) == 256


def test_uncertain_training_label_rejected():
    with pytest.raises(ValueError, match='label'):
        select_training_rows([dict(safe_text='x', label='uncertain', split='train')])


def test_real_tokenizer_and_binary_head():
    torch = pytest.importorskip('torch', reason='ModernBERT requires the dedicated v3 environment')
    if not Path('models/benchmark_v3/modernbert_base_source/model.safetensors').exists():
        pytest.skip('Pinned source checkpoint must first be downloaded')
    from src.benchmark_v3.modernbert import load_classifier
    torch.set_num_threads(4)
    tokenizer, model = load_classifier()
    model.eval()
    with torch.no_grad():
        logits = model(**tokenizer(['Fictional bank statement', 'Fictional urgent account notice'],
                                   padding=True, return_tensors='pt')).logits
    assert tuple(logits.shape) == (2, 2)
    probabilities = logits.softmax(-1)
    assert torch.all((probabilities >= 0) & (probabilities <= 1))
    assert torch.allclose(probabilities.sum(-1), torch.ones(2))


def test_frozen_model_rejects_tampering(tmp_path):
    import hashlib
    import json
    weights = tmp_path / 'weights.bin'
    weights.write_bytes(b'original')
    (tmp_path / 'model_manifest.json').write_text(json.dumps({
        'files': {'weights.bin': hashlib.sha256(b'original').hexdigest()}}))
    assert verify_frozen_model(tmp_path)
    weights.write_bytes(b'tampered')
    with pytest.raises(ValueError, match='integrity'):
        verify_frozen_model(tmp_path)


def test_training_refuses_changed_protocol_before_read_or_model_load(monkeypatch):
    from src.benchmark_v3 import modernbert, protocol
    def changed_protocol(experiment):
        assert experiment == 'primary'
        raise ValueError('changed protocol hash')
    monkeypatch.setattr(protocol, 'verify_frozen_inputs', changed_protocol)
    with pytest.raises(ValueError, match='changed protocol hash'):
        modernbert.train('modeling_cohort.csv', 'unused_output', {})


def test_training_refuses_alternate_csv_with_wrong_frozen_hash(monkeypatch):
    from src.benchmark_v3 import modernbert, protocol
    monkeypatch.setattr(protocol, 'verify_frozen_inputs', lambda _: {'cohort_sha256': 'expected'})
    monkeypatch.setattr(modernbert, 'sha256', lambda _: 'changed')
    with pytest.raises(ValueError, match='frozen cohort hash'):
        modernbert.train('alternate/modeling_cohort.csv', 'unused_output', {})


@pytest.fixture
def frozen_training_cache(tmp_path, monkeypatch):
    import builtins
    import json
    from src.benchmark_v3 import modernbert, protocol
    frozen_csv = tmp_path / 'modeling_cohort.csv'
    frozen_csv.write_text('not read when returning a frozen model')
    digest = modernbert.sha256(frozen_csv)
    requested = json.loads(Path('configs/benchmark_v3/modernbert_training.json').read_text())
    saved = dict(requested, frozen_csv_sha256=digest, max_length=128)
    output = tmp_path / 'frozen_model'
    output.mkdir()
    (output / 'training_config.json').write_text(json.dumps(saved))
    (output / 'weights.bin').write_bytes(b'frozen weights sentinel')
    manifest = {'files': {p.name: modernbert.sha256(p) for p in output.iterdir()}}
    (output / 'model_manifest.json').write_text(json.dumps(manifest))
    monkeypatch.setattr(protocol, 'verify_frozen_inputs', lambda _: {'cohort_sha256': digest})
    original_import = builtins.__import__
    def no_torch(name, *args, **kwargs):
        if name == 'torch':
            raise AssertionError('Frozen cache must return or reject before importing torch')
        return original_import(name, *args, **kwargs)
    monkeypatch.setattr(builtins, '__import__', no_torch)
    return modernbert, frozen_csv, output, requested, manifest


def test_identical_training_request_returns_frozen_cache_without_changes(frozen_training_cache):
    modernbert, frozen_csv, output, requested, manifest = frozen_training_cache
    before = {p.name: p.read_bytes() for p in output.iterdir()}
    assert modernbert.train(frozen_csv, output, requested) == manifest
    assert before == {p.name: p.read_bytes() for p in output.iterdir()}


@pytest.mark.parametrize('field,value', [
    ('learning_rate', .1), ('batch_size', 99), ('epochs', 99), ('weight_decay', .5),
    ('warmup', 10), ('random_seed', 123), ('optimizer', 'SGD'), ('scheduler', 'linear'),
    ('decision_threshold', .8), ('reference_compile', True), ('attn_implementation', 'eager')])
def test_changed_training_settings_cannot_overwrite_frozen_cache(frozen_training_cache, field, value):
    modernbert, frozen_csv, output, requested, _ = frozen_training_cache
    before = {p.name: p.read_bytes() for p in output.iterdir()}
    with pytest.raises(ValueError, match='frozen training configuration'):
        modernbert.train(frozen_csv, output, dict(requested, **{field: value}))
    assert before == {p.name: p.read_bytes() for p in output.iterdir()}


def test_changed_cohort_cannot_reuse_frozen_training_cache(frozen_training_cache, monkeypatch):
    import json
    modernbert, frozen_csv, output, requested, _ = frozen_training_cache
    config_path = output / 'training_config.json'
    saved = json.loads(config_path.read_text())
    saved['frozen_csv_sha256'] = 'different original training input'
    config_path.write_text(json.dumps(saved))
    monkeypatch.setattr(modernbert, 'verify_frozen_model', lambda _: True)
    with pytest.raises(ValueError, match='frozen training cohort'):
        modernbert.train(frozen_csv, output, requested)
