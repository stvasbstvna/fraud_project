from __future__ import annotations

import contextlib
import io
import json
import tempfile
import unittest
from pathlib import Path

import pandas as pd

from src.generate_llm_rewrites_openai import (
    DEFAULT_MODEL,
    run_generation,
    select_generation_targets,
)


ROOT = Path(__file__).resolve().parents[1]


def row(pair_id: str, status: str, attempts: int = 0) -> dict[str, object]:
    return {
        "pair_id": pair_id,
        "original_id": f"source-{pair_id}",
        "source_dataset": "test",
        "true_label": "phishing",
        "binary_label": 1,
        "intent_type": "account_alert",
        "requested_action": "follow_link",
        "original_text": f"Original {pair_id} [URL]",
        "condition": "T1_llm_neutral_rewrite",
        "text": "Existing rewrite [URL]" if status == "completed" else "",
        "prompt_id": "neutral_rewrite_v1",
        "generator_model": DEFAULT_MODEL,
        "response_id": "existing-response" if status == "completed" else "",
        "generated_at_utc": "",
        "generation_status": status,
        "generation_attempts": attempts,
        "rejection_reason": "rewrite equals original" if status == "rejected_safety_check" else "",
        "safety_check_passed": status == "completed",
        "human_review_status": "pending",
        "semantic_intent_preserved": "true" if status == "completed" else "pending",
        "requested_action_preserved": "true" if status == "completed" else "pending",
        "label_preserved": "true" if status == "completed" else "pending",
        "review_notes": "",
    }


class FakeResponses:
    def __init__(self, outcome=None):
        self.outcome = outcome
        self.calls: list[dict] = []

    def create(self, **kwargs):
        self.calls.append(kwargs)
        if isinstance(self.outcome, Exception):
            raise self.outcome
        pair_id = kwargs["input"].splitlines()[0].split(": ", 1)[1]
        original_id = kwargs["input"].splitlines()[1].split(": ", 1)[1]
        payload = {
            "pair_id": pair_id,
            "original_id": original_id,
            "rewrite_text": f"Rewritten {pair_id} [URL]",
            "semantic_intent_preserved": True,
            "requested_action_preserved": True,
            "label_preserved": True,
            "operational_detail_added": False,
        }
        return type("Response", (), {"id": f"response-{pair_id}", "output_text": json.dumps(payload)})()


class FakeClient:
    def __init__(self, outcome=None):
        self.responses = FakeResponses(outcome)


class FakeRateLimitError(Exception):
    def __init__(self, message: str, retry_after: str = "30 seconds"):
        super().__init__(message)
        self.retry_after = retry_after


class ResumableGenerationTests(unittest.TestCase):
    def setUp(self):
        self.frame = pd.DataFrame([
            row("completed", "completed", 1),
            row("rejected-one", "rejected_safety_check", 1),
            row("rejected-max", "rejected_safety_check", 2),
            row("pending-one", "pending", 0),
            row("pending-two", "pending", 0),
        ])

    def test_rejected_rows_are_skipped_by_default_and_completed_never_selected(self):
        target = select_generation_targets(self.frame)
        self.assertEqual(target["pair_id"].tolist(), ["pending-one", "pending-two"])

    def test_pending_rows_are_processed_before_rejected(self):
        target = select_generation_targets(self.frame, retry_rejected=True, max_attempts=2)
        self.assertEqual(
            target["pair_id"].tolist(),
            ["pending-one", "pending-two", "rejected-one"],
        )

    def test_retry_rejected_flag_and_maximum_attempts(self):
        without_retry = select_generation_targets(self.frame, retry_rejected=False, max_attempts=3)
        self.assertNotIn("rejected-one", without_retry["pair_id"].tolist())
        with_retry = select_generation_targets(self.frame, retry_rejected=True, max_attempts=2)
        self.assertIn("rejected-one", with_retry["pair_id"].tolist())
        self.assertNotIn("rejected-max", with_retry["pair_id"].tolist())

    def test_rate_limit_preserves_csv_and_current_row_without_traceback(self):
        with tempfile.TemporaryDirectory(dir=ROOT) as temp:
            path = Path(temp) / "pairs.csv"
            frame = pd.DataFrame([row("pending-one", "pending", 0)])
            frame.to_csv(path, index=False, lineterminator="\n")
            before = path.read_bytes()
            client = FakeClient(FakeRateLimitError("quota reached", "30 seconds"))
            output = io.StringIO()
            with contextlib.redirect_stdout(output):
                finished = run_generation(
                    frame,
                    input_path=path,
                    client=client,
                    rate_limit_error=FakeRateLimitError,
                    model=DEFAULT_MODEL,
                    pause_seconds=0,
                )
            self.assertFalse(finished)
            self.assertEqual(path.read_bytes(), before)
            self.assertEqual(frame.loc[0, "generation_attempts"], 0)
            self.assertEqual(frame.loc[0, "generation_status"], "pending")
            message = output.getvalue()
            self.assertIn("Rate limit: quota reached", message)
            self.assertIn("Retry time: 30 seconds", message)
            self.assertIn("completed=0, rejected=0, pending=1", message)
            self.assertNotIn("Traceback", message)

    def test_successful_response_increments_only_selected_row_and_saves(self):
        with tempfile.TemporaryDirectory(dir=ROOT) as temp:
            path = Path(temp) / "pairs.csv"
            frame = pd.DataFrame([
                row("completed", "completed", 1),
                row("pending-one", "pending", 0),
            ])
            frame.to_csv(path, index=False, lineterminator="\n")
            client = FakeClient()
            finished = run_generation(
                frame,
                input_path=path,
                client=client,
                rate_limit_error=FakeRateLimitError,
                model=DEFAULT_MODEL,
                pause_seconds=0,
            )
            self.assertTrue(finished)
            self.assertEqual(len(client.responses.calls), 1)
            self.assertEqual(frame.loc[0, "generation_attempts"], 1)
            self.assertEqual(frame.loc[0, "response_id"], "existing-response")
            self.assertEqual(frame.loc[1, "generation_attempts"], 1)
            self.assertEqual(frame.loc[1, "generation_status"], "completed")
            saved = pd.read_csv(path, keep_default_na=False)
            self.assertEqual(saved.loc[1, "generation_attempts"], 1)


if __name__ == "__main__":
    unittest.main()
