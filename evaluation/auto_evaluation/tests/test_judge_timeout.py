"""Tests for the message when the judge does not finish in the time limit."""

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from deepeval.models.base_model import DeepEvalBaseLLM

from auto_evaluation.eval_main import EvaluationHarness, JudgeTimeoutError


def test_judge_timeout_names_the_cause_and_the_next_step(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.chdir(tmp_path)
    harness = object.__new__(EvaluationHarness)
    harness.qns = [
        {"question": f"question {i}", "ground_truth": "truth"} for i in range(3)
    ]
    harness.eval_model = MagicMock(spec=DeepEvalBaseLLM)
    harness.eval_model.get_model_name.return_value = "gemini-judge"
    answer = {
        "response": "ok",
        "context_sources": [{"source": "doc", "context": "ctx"}],
        "tools": [],
    }

    with (
        patch.object(harness, "query", return_value=(answer, 1.0)),
        patch("auto_evaluation.eval_main.evaluate", side_effect=TimeoutError),
        pytest.raises(JudgeTimeoutError) as error,
    ):
        harness.evaluate("agent-retriever", metadata={"judge": "gemini-judge"})

    message = str(error.value)
    assert "the judge gemini-judge did not score all 3 test cases" in message
    assert "Run the job again" in message
    assert "DEEPEVAL_PER_TASK_TIMEOUT_SECONDS_OVERRIDE" in message
