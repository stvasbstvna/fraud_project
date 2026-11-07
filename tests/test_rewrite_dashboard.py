from __future__ import annotations

import hashlib
import tempfile
import unittest
from pathlib import Path

import pandas as pd

from src.build_rewrite_dashboard import build_dashboard, compute_progress


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def sample_pairs() -> pd.DataFrame:
    rows = []
    states = [
        ("completed", "pending", "phishing", 1, "SmishTank"),
        ("completed", "approved", "phishing", 1, "SmishTank"),
        ("rejected_safety_check", "pending", "non_phishing", 0, "SmishX"),
        ("pending", "pending", "phishing", 1, "SmishX"),
    ]
    for index, (status, review, label, binary, source) in enumerate(states, 1):
        pair_id = f"P{index:03d}"
        common = {
            "pair_id": pair_id, "original_id": f"source-{index}",
            "source_dataset": source, "true_label": label, "binary_label": binary,
            "original_text": f"Defanged message {index} [URL]", "generator_model": "gpt-test",
            "rejection_reason": "live URL" if "rejected" in status else "",
        }
        rows.append({
            **common, "condition": "T0_original", "text": common["original_text"],
            "generation_status": "original", "safety_check_passed": True,
            "human_review_status": "not_applicable",
        })
        rows.append({
            **common, "condition": "T1_llm_neutral_rewrite",
            "text": f"Reworded defanged message {index} [URL]" if status == "completed" else "",
            "generation_status": status, "safety_check_passed": status == "completed",
            "human_review_status": review,
        })
    return pd.DataFrame(rows)


class RewriteDashboardTests(unittest.TestCase):
    def test_progress_counting(self):
        progress = compute_progress(sample_pairs())
        self.assertEqual(progress, {
            "total_pairs": 4, "completed": 2, "pending": 1, "rejected": 1, "approved": 1,
        })

    def test_generation_without_evaluation_files_and_source_immutability(self):
        with tempfile.TemporaryDirectory(dir=Path.cwd()) as temp:
            root = Path(temp)
            pairs_path = root / "rewrite_pairs.csv"
            sample_pairs().to_csv(pairs_path, index=False)
            before = digest(pairs_path)
            index = build_dashboard(pairs_path, root / "empty-results", root / "dashboard")
            self.assertTrue(index.exists())
            self.assertTrue((root / "dashboard/figures/generation_progress.png").exists())
            self.assertEqual(digest(pairs_path), before)
            page = index.read_text(encoding="utf-8")
            self.assertIn("evaluation metrics are not available", page)

    def test_generation_with_evaluation_files(self):
        with tempfile.TemporaryDirectory(dir=Path.cwd()) as temp:
            root = Path(temp)
            results = root / "results"
            results.mkdir()
            pairs_path = root / "rewrite_pairs.csv"
            sample_pairs().to_csv(pairs_path, index=False)
            metrics = pd.DataFrame([
                {"model": "tfidf_logistic_regression", "condition": condition, "rows": 2,
                 "accuracy": 1.0, "precision": 1.0, "recall": 1.0, "f1": 1.0,
                 "specificity": "", "false_positive_rate": "", "balanced_accuracy": "",
                 "false_negative_rate": 0.0, "mean_phishing_probability": probability}
                for condition, probability in (("T0_original", 0.8), ("T1_llm_neutral_rewrite", 0.7))
            ])
            metrics.to_csv(results / "metrics_by_model_and_condition.csv", index=False)
            predictions = pd.DataFrame([
                {"model": "tfidf_logistic_regression", "pair_id": pair_id,
                 "condition": condition, "binary_label": label, "predicted_binary_label": prediction,
                 "phishing_probability": probability, "text": text}
                for pair_id, label, before, after in (("P001", 1, 1, 0), ("P002", 0, 0, 0))
                for condition, prediction, probability, text in (
                    ("T0_original", before, 0.8 if label else 0.2, "Original [URL]"),
                    ("T1_llm_neutral_rewrite", after, 0.5 if label else 0.3, "Rewrite [URL]"),
                )
            ])
            predictions.to_csv(results / "paired_predictions.csv", index=False)
            pd.DataFrame([
                {"model": "tfidf_logistic_regression", "true_label": "phishing",
                 "prediction_original": 1, "prediction_rewrite": 0, "rows": 1}
            ]).to_csv(results / "paired_transition_table.csv", index=False)
            pd.DataFrame([{
                "model": "tfidf_logistic_regression", "phishing_pairs": 1,
                "original_recall": 1.0, "rewrite_recall": 0.0, "recall_drop": 1.0,
                "original_fnr": 0.0, "rewrite_fnr": 1.0, "originally_detected": 1,
                "became_false_negative": 1, "attack_success_rate": 1.0,
                "mean_confidence_drop": 0.3, "confidence_drop_ci95_low": 0.3,
                "confidence_drop_ci95_high": 0.3, "mcnemar_exact_p_value": 1.0,
            }]).to_csv(results / "statistical_tests.csv", index=False)

            index = build_dashboard(pairs_path, results, root / "dashboard")
            self.assertTrue(index.exists())
            for figure in (
                "detector_performance.png", "confusion_matrices.png", "paired_transitions.png",
                "confidence_drop_histograms.png", "confidence_scatter.png",
            ):
                self.assertTrue((root / "dashboard/figures" / figure).exists(), figure)

    def test_missing_optional_metrics_are_rendered_as_na(self):
        with tempfile.TemporaryDirectory(dir=Path.cwd()) as temp:
            root = Path(temp)
            results = root / "results"
            results.mkdir()
            pairs_path = root / "rewrite_pairs.csv"
            sample_pairs().to_csv(pairs_path, index=False)
            pd.DataFrame([{
                "model": "tfidf_logistic_regression", "condition": "T0_original",
                "accuracy": 0.9, "precision": 0.9, "recall": 0.9, "f1": 0.9,
            }]).to_csv(results / "metrics_by_model_and_condition.csv", index=False)
            index = build_dashboard(pairs_path, results, root / "dashboard")
            self.assertIn("N/A", index.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
