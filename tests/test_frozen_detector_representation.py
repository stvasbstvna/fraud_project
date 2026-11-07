from pathlib import Path

import hashlib
import joblib
import pytest


ROOT = Path(__file__).resolve().parents[1]
pytestmark = pytest.mark.filterwarnings(
    "ignore:Setting the shape on a NumPy array has been deprecated:DeprecationWarning"
)
EXPECTED = {
    "tfidf_logistic_regression.joblib": "84ba84863ce9a8fd757cd4e9babc6dacf39496223299a06df0054f94ca688fcc",
    "tfidf_random_forest.joblib": "99c4a06e7ad52ff000c0a1d8818ca61cdc268d929a1a970e79d74b6e0c38b4fc",
}


def test_frozen_model_hashes_and_vectorizer_metadata_match_documentation():
    for name, expected_hash in EXPECTED.items():
        path = ROOT / "models/final" / name
        assert hashlib.sha256(path.read_bytes()).hexdigest() == expected_hash
        vectorizer = joblib.load(path).named_steps["tfidf"]
        assert vectorizer.analyzer == "word"
        assert vectorizer.ngram_range == (1, 2)
        assert vectorizer.lowercase is True
        assert vectorizer.min_df == 2
        assert vectorizer.max_df == 0.95
        assert vectorizer.sublinear_tf is True
        assert vectorizer.stop_words == "english"
        assert vectorizer.tokenizer is None


def test_model_specific_feature_caps():
    lr = joblib.load(ROOT / "models/final/tfidf_logistic_regression.joblib")
    rf = joblib.load(ROOT / "models/final/tfidf_random_forest.joblib")
    assert lr.named_steps["tfidf"].max_features == 50_000
    assert rf.named_steps["tfidf"].max_features == 20_000
