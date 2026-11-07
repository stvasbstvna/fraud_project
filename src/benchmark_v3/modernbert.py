"""Pinned ModernBERT binary classifier; test partitions never enter fitting."""
import csv
from datetime import datetime, timezone
import hashlib
import json
import math
from pathlib import Path
import time

MODEL_ID = 'answerdotai/ModernBERT-base'
REVISION = '8949b909ec900327062f0ebf497f51aef5e6f0c8'
SOURCE = Path('models/benchmark_v3/modernbert_base_source')


def save_json(path, data):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2), encoding='utf-8')


def sha256(path):
    digest = hashlib.sha256()
    with open(path, 'rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            digest.update(block)
    return digest.hexdigest()


def select_training_rows(rows):
    partitions = {'train': [], 'validation': []}
    labels = {'legitimate': 0, 'phishing': 1, '0': 0, '1': 1}
    for row in rows:
        if row['split'] not in partitions:
            continue
        label = str(row['label'])
        if label not in labels:
            raise ValueError('Unsupported training label: ' + label)
        if not isinstance(row['safe_text'], str) or not row['safe_text'].strip():
            raise ValueError('Empty safe_text in fitting partition')
        partitions[row['split']].append((row['safe_text'], labels[label]))
    return partitions['train'], partitions['validation']


def choose_max_length(lengths):
    if not lengths:
        raise ValueError('No train/validation lengths')
    lengths = sorted(lengths)
    percentile = lengths[min(len(lengths)-1, math.ceil(.99 * len(lengths))-1)]
    return 128 if percentile <= 128 else 256


def hardware():
    import platform
    import psutil
    import torch
    device = 'cuda' if torch.cuda.is_available() else 'mps' if torch.backends.mps.is_available() else 'cpu'
    return dict(device=device, cuda_available=torch.cuda.is_available(),
                mps_available=torch.backends.mps.is_available(), platform=platform.platform(),
                processor=platform.processor(), logical_cpus=psutil.cpu_count(),
                total_ram_bytes=psutil.virtual_memory().total,
                available_ram_bytes=psutil.virtual_memory().available, torch=torch.__version__)


def download():
    from huggingface_hub import HfApi, snapshot_download
    import transformers
    info = HfApi().model_info(MODEL_ID, revision=REVISION, files_metadata=True)
    revision = info.sha
    wanted = ['config.json', 'model.safetensors', 'tokenizer.json',
              'tokenizer_config.json', 'special_tokens_map.json', 'README.md']
    missing = []
    for name in wanted:
        path = SOURCE / name
        sibling = next(s for s in info.siblings if s.rfilename == name)
        if not path.exists() or path.stat().st_size != sibling.size:
            missing.append(name)
        elif sibling.lfs and sha256(path) != sibling.lfs.sha256:
            missing.append(name)
    if missing:
        snapshot_download(MODEL_ID, revision=revision, local_dir=str(SOURCE),
                          allow_patterns=missing, max_workers=2)
    manifest = dict(model_id=MODEL_ID, revision=revision, transformers=transformers.__version__,
                    retrieved_at_utc=datetime.now(timezone.utc).isoformat(),
                    files={name: sha256(SOURCE / name) for name in wanted})
    save_json('models/benchmark_v3/modernbert_source_manifest.json', manifest)
    return manifest


def load_classifier():
    from transformers import AutoModelForSequenceClassification, AutoTokenizer
    tokenizer = AutoTokenizer.from_pretrained(SOURCE, local_files_only=True)
    model = AutoModelForSequenceClassification.from_pretrained(
        SOURCE, num_labels=2, local_files_only=True, reference_compile=False,
        attn_implementation='sdpa', id2label={0: 'legitimate', 1: 'phishing'},
        label2id={'legitimate': 0, 'phishing': 1})
    return tokenizer, model


def feasibility():
    """Synthetic engineering fixture ONLY, never a research experiment."""
    import torch
    import psutil
    import transformers
    transformers.set_seed(42)
    torch.set_num_threads(min(4, torch.get_num_threads()))
    info = hardware()
    tokenizer, model = load_classifier()
    model.to(info['device']).train()
    texts = ['SYNTHETIC FEASIBILITY FIXTURE: Your fictional bank statement is ready.',
             'SYNTHETIC FEASIBILITY FIXTURE: Fictional account suspended, verify now.']
    batch = tokenizer(texts, padding='max_length', truncation=True, max_length=128, return_tensors='pt')
    batch = {k: v.to(info['device']) for k, v in batch.items()}
    labels = torch.tensor([0, 1], device=info['device'])
    optimizer = torch.optim.AdamW(model.parameters(), lr=2e-5, weight_decay=.01)
    steps = []
    for step in range(2):
        started = time.perf_counter()
        optimizer.zero_grad(set_to_none=True)
        output = model(**batch, labels=labels)
        assert tuple(output.logits.shape) == (2, 2)
        probabilities = output.logits.softmax(-1)
        assert torch.all((probabilities >= 0) & (probabilities <= 1))
        output.loss.backward()
        optimizer.step()
        steps.append(dict(step=step+1, loss=float(output.loss.detach().cpu()), seconds=time.perf_counter()-started))
    result = dict(status='NOT_RESEARCH_SYNTHETIC_FEASIBILITY_ONLY', hardware=info,
                  seed=42, batch_size=2, max_length=128, optimizer='AdamW',
                  all_parameters_trainable=True, parameters=sum(p.numel() for p in model.parameters()), steps=steps)
    result['process_memory_bytes'] = psutil.Process().memory_info()._asdict()
    result['estimated_training_seconds_per_epoch_at_128_tokens'] = {
        str(size): math.ceil(size / 2) * steps[-1]['seconds'] for size in [100, 1000, 10000]}
    save_json('models/benchmark_v3/modernbert_feasibility.json', result)
    return result


def train(frozen_csv, output_dir, config):
    from .protocol import verify_frozen_inputs
    frozen_csv = Path(frozen_csv).resolve()
    choices = {'modeling_cohort.csv': ('primary', 'cohort_sha256'),
               'source_holdout_cohort.csv': ('source_holdout', 'source_holdout_cohort_sha256')}
    if frozen_csv.name not in choices:
        raise ValueError('Unrecognized frozen cohort filename')
    experiment, hash_key = choices[frozen_csv.name]
    freeze = verify_frozen_inputs(experiment)
    if sha256(frozen_csv) != freeze[hash_key]:
        raise ValueError('Supplied CSV does not match frozen cohort hash')
    output_dir = Path(output_dir)
    if (output_dir / 'model_manifest.json').exists():
        verify_frozen_model(output_dir)
        saved = json.loads((output_dir / 'training_config.json').read_text())
        if saved.get('frozen_csv_sha256') != freeze[hash_key]:
            raise ValueError('Cannot reuse a different frozen training cohort')
        defaults = dict(model_id=MODEL_ID, learning_rate=2e-5, batch_size=2, epochs=2,
                        weight_decay=.01, warmup=0, random_seed=42, optimizer='AdamW',
                        scheduler='constant', decision_threshold=.5,
                        reference_compile=False, attn_implementation='sdpa')
        for key, default in defaults.items():
            if saved.get(key) != config.get(key, default):
                raise ValueError('Cannot change frozen training configuration: ' + key)
        if isinstance(config.get('max_length'), int) and config['max_length'] != saved.get('max_length'):
            raise ValueError('Cannot change frozen training configuration: max_length')
        return json.loads((output_dir / 'model_manifest.json').read_text())
    import torch
    from transformers import set_seed
    set_seed(config.get('random_seed', 42))
    torch.set_num_threads(min(4, torch.get_num_threads()))
    with open(frozen_csv, encoding='utf-8', newline='') as stream:
        train_rows, validation = select_training_rows(csv.DictReader(stream))
    if not train_rows or not validation or len({y for _, y in train_rows}) != 2:
        raise ValueError('Training needs both labels and nonempty validation')
    output_dir.mkdir(parents=True, exist_ok=True)
    tokenizer, model = load_classifier()
    lengths = [len(tokenizer.encode(text)) for text, _ in train_rows + validation]
    max_length = choose_max_length(lengths)
    resolved = dict(config, max_length=max_length, max_length_policy='99th percentile train+validation; 128 or 256',
                    frozen_csv_sha256=sha256(frozen_csv), optimizer='AdamW', scheduler='constant', warmup=0,
                    early_stopping=False, checkpoint_selection='minimum validation cross entropy', hardware=hardware())
    sorted_lengths = sorted(lengths)
    resolved['fitting_token_lengths'] = dict(
        count=len(lengths), maximum=max(lengths),
        p50=sorted_lengths[math.ceil(.50 * len(lengths))-1],
        p95=sorted_lengths[math.ceil(.95 * len(lengths))-1],
        p99=sorted_lengths[math.ceil(.99 * len(lengths))-1],
        fraction_truncated=sum(n > max_length for n in lengths) / len(lengths))
    device = resolved['hardware']['device']
    model.to(device)
    optimizer = torch.optim.AdamW(model.parameters(), lr=config.get('learning_rate', 2e-5),
                                 weight_decay=config.get('weight_decay', .01))
    batch_size = config.get('batch_size', 2)
    def batches(rows):
        for offset in range(0, len(rows), batch_size):
            values = rows[offset:offset+batch_size]
            encoded = tokenizer([x for x, _ in values], padding=True, truncation=True,
                                max_length=max_length, return_tensors='pt')
            yield {k: v.to(device) for k, v in encoded.items()}, torch.tensor([y for _, y in values], device=device)
    history = []
    best = float('inf')
    for epoch in range(config.get('epochs', 2)):
        model.train()
        order = torch.randperm(len(train_rows)).tolist()
        losses = []
        for batch, labels in batches([train_rows[i] for i in order]):
            optimizer.zero_grad(set_to_none=True)
            loss = model(**batch, labels=labels).loss
            loss.backward()
            optimizer.step()
            losses.append(float(loss.detach().cpu()))
        model.eval()
        with torch.no_grad():
            values = [(float(model(**batch, labels=labels).loss.cpu()), len(labels)) for batch, labels in batches(validation)]
        val_loss = sum(loss * count for loss, count in values) / sum(count for _, count in values)
        history.append(dict(epoch=epoch+1, train_loss=sum(losses)/len(losses), validation_loss=val_loss))
        if val_loss < best:
            best = val_loss
            model.save_pretrained(output_dir / 'best_checkpoint', safe_serialization=True)
            tokenizer.save_pretrained(output_dir / 'best_checkpoint')
            save_json(output_dir / 'trainer_state.json', dict(best_epoch=epoch+1, best_validation_loss=best))
    save_json(output_dir / 'training_config.json', resolved)
    save_json(output_dir / 'metrics_history.json', history)
    manifest = dict(model_id=MODEL_ID, source_manifest=json.loads(Path('models/benchmark_v3/modernbert_source_manifest.json').read_text()),
                    files={str(p.relative_to(output_dir)): sha256(p) for p in output_dir.rglob('*')
                           if p.is_file() and p.name != 'model_manifest.json'})
    save_json(output_dir / 'model_manifest.json', manifest)
    return manifest


def verify_frozen_model(output_dir):
    output_dir = Path(output_dir)
    manifest = json.loads((output_dir / 'model_manifest.json').read_text())
    for name, expected in manifest['files'].items():
        path = output_dir / name
        if not path.is_file() or sha256(path) != expected:
            raise ValueError('Frozen model integrity failure: ' + name)
    return True


def predict_proba(texts, checkpoint, batch_size=2):
    """Evaluate a frozen best checkpoint without updating any weights."""
    import torch
    from transformers import AutoModelForSequenceClassification, AutoTokenizer
    verify_frozen_model(Path(checkpoint).parent)
    torch.set_num_threads(min(4, torch.get_num_threads()))
    tokenizer = AutoTokenizer.from_pretrained(checkpoint, local_files_only=True)
    model = AutoModelForSequenceClassification.from_pretrained(
        checkpoint, local_files_only=True, reference_compile=False, attn_implementation='sdpa')
    device = hardware()['device']
    model.to(device).eval()
    training_config = Path(checkpoint).parent / 'training_config.json'
    max_length = json.loads(training_config.read_text())['max_length']
    result = []
    with torch.no_grad():
        for start in range(0, len(texts), batch_size):
            batch = tokenizer(texts[start:start+batch_size], padding=True, truncation=True,
                              max_length=max_length, return_tensors='pt')
            logits = model(**{k: v.to(device) for k, v in batch.items()}).logits
            result.extend(logits.softmax(-1)[:, 1].cpu().tolist())
    return result


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('action', choices=['download', 'feasibility'])
    args = parser.parse_args()
    print(json.dumps(download() if args.action == 'download' else feasibility(), indent=2))
