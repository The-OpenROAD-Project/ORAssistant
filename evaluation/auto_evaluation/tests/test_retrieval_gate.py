"""Tests for the check that stops an eval run when retrieval comes back empty."""

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from deepeval.models.base_model import DeepEvalBaseLLM

from auto_evaluation.eval_main import (
    EmptyRetrievalError,
    EvaluationHarness,
    check_retrieval,
)


def _answer(context: list[str], response: str = "ok") -> dict:
    """Build a backend response like the one /conversations/agent-retriever sends."""
    return {
        "response": response,
        "context_sources": [{"source": "doc", "context": c} for c in context],
        "tools": [],
    }


def test_run_fails_when_too_many_questions_have_no_context() -> None:
    results = [(f"good question {i}", _answer(["ctx"])) for i in range(8)]
    results += [
        ("What is CTS?", _answer([])),
        ("How do I run placement?", _answer([])),
    ]

    with pytest.raises(EmptyRetrievalError) as error:
        check_retrieval(results)

    message = str(error.value)
    assert "2 of 10 questions" in message
    assert "What is CTS?" in message
    assert "How do I run placement?" in message


def test_an_invalid_answer_counts_as_empty() -> None:
    results = [(f"good question {i}", _answer(["ctx"])) for i in range(3)]
    results.append(("What is STA?", _answer(["ctx"], response=" Invalid\n")))

    with pytest.raises(EmptyRetrievalError, match="1 of 4 questions"):
        check_retrieval(results)


def test_run_passes_at_the_limit() -> None:
    results = [(f"good question {i}", _answer(["ctx"])) for i in range(9)]
    results.append(("What is CTS?", _answer([])))

    check_retrieval(results)


def test_harness_stops_before_the_judge_when_retrieval_is_empty(
    capsys: pytest.CaptureFixture[str],
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    # A stopped run writes its results file to the working directory.
    monkeypatch.chdir(tmp_path)
    harness = object.__new__(EvaluationHarness)
    harness.qns = [
        {"question": f"question {i}", "ground_truth": "truth"} for i in range(5)
    ]
    harness.eval_model = MagicMock(spec=DeepEvalBaseLLM)
    # Stand-in for the backend: every answer comes back without context.
    backend_answer = (_answer([], response="invalid"), 1.0)

    with (
        patch.object(harness, "query", return_value=backend_answer),
        patch("auto_evaluation.eval_main.evaluate") as judge,
        pytest.raises(EmptyRetrievalError, match="5 of 5 questions"),
    ):
        harness.evaluate("agent-retriever", metadata={"judge": "j"})

    judge.assert_not_called()
    # A stopped run still names its setup.
    assert "Run metadata: judge=j" in capsys.readouterr().out.splitlines()
