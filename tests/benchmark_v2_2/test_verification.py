import csv
import hashlib
import pytest


def test_historical_verifier_detects_changed_or_missing_evidence(tmp_path):
    from src.benchmark_v2_2.verify import verify_baseline
    old = tmp_path / 'old.txt'; old.write_text('original')
    inventory = tmp_path / 'inventory.csv'
    with inventory.open('w', newline='') as handle:
        writer = csv.DictWriter(handle, fieldnames=['path', 'sha256']); writer.writeheader()
        writer.writerow({'path': 'old.txt', 'sha256': hashlib.sha256(old.read_bytes()).hexdigest()})
    assert verify_baseline(tmp_path, inventory) == 1
    old.write_text('changed')
    with pytest.raises(ValueError, match='historical'):
        verify_baseline(tmp_path, inventory)
    old.unlink()
    with pytest.raises(ValueError, match='historical'):
        verify_baseline(tmp_path, inventory)
