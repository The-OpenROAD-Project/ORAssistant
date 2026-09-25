"""Tests for the retrieval record that the eval keeps for each case."""

import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from deepeval.models.base_model import DeepEvalBaseLLM

from auto_evaluation import eval_cases
from auto_evaluation.eval_main import EmptyRetrievalError, EvaluationHarness


def _answer(sources: list[str], tools: list[str], response: str = "ok") -> dict:
    """Build a backend response like the one /conversations/agent-retriever sends."""
    return {
        "response": response,
        "context_sources": [{"source": s, "context": f"text of {s}"} for s in sources],
        "tools": tools,
    }


def _harness(question_count: int) -> EvaluationHarness:
    harness = object.__new__(EvaluationHarness)
    harness.eval_model = MagicMock(spec=DeepEvalBaseLLM)
    harness.qns = [
        {"question": f"question {i}", "ground_truth": "truth"}
        for i in range(question_count)
    ]
    return harness


def _read_cases(directory: Path) -> list[dict]:
    lines = (directory / eval_cases.CASES_FILE).read_text().splitlines()
    return [json.loads(line) for line in lines]


def test_each_case_names_its_tool_and_sources(
    capsys: pytest.CaptureFixture[str],
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.chdir(tmp_path)
    harness = _harness(2)
    answers = [
        (_answer(["https://a", "https://b"], ["retrieve_cmds"]), 1.0),
        (_answer(["https://c"], []), 1.0),
    ]

    with (
        patch.object(harness, "query", side_effect=answers),
        patch("auto_evaluation.eval_main.evaluate") as judge,
    ):
        harness.evaluate("agent-retriever", metadata={"judge": "j"})

    lines = capsys.readouterr().out.splitlines()
    assert "Case 0: tool=retrieve_cmds sources=[https://a,https://b]" in lines
    assert "Case 1: tool=unknown sources=[https://c]" in lines
    assert _read_cases(tmp_path) == [
        {
            "index": 0,
            "question": "question 0",
            "tool": "retrieve_cmds",
            "sources": ["https://a", "https://b"],
        },
        {
            "index": 1,
            "question": "question 1",
            "tool": "unknown",
            "sources": ["https://c"],
        },
    ]
    test_cases = judge.call_args.kwargs["test_cases"]
    assert [tc.name for tc in test_cases] == ["test_case_0", "test_case_1"]
    assert test_cases[0].additional_metadata == {
        "tool": "retrieve_cmds",
        "sources": ["https://a", "https://b"],
    }
    # The judge still scores the context text, not the source URLs.
    assert test_cases[0].retrieval_context == ["text of https://a", "text of https://b"]


def test_a_stopped_run_keeps_its_case_records(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.chdir(tmp_path)
    harness = _harness(3)
    empty = (_answer([], ["retrieve_general"], response="invalid"), 1.0)

    with (
        patch.object(harness, "query", return_value=empty),
        patch("auto_evaluation.eval_main.evaluate"),
        pytest.raises(EmptyRetrievalError),
    ):
        harness.evaluate("agent-retriever", metadata={"judge": "j"})

    assert [case["index"] for case in _read_cases(tmp_path)] == [0, 1, 2]


def test_query_asks_the_backend_for_sources_and_context() -> None:
    harness = object.__new__(EvaluationHarness)
    harness.base_url = "http://backend"

    with (
        patch("auto_evaluation.eval_main.time.sleep"),
        patch("auto_evaluation.eval_main.requests.post") as post,
    ):
        harness.query("agent-retriever", "What is OpenROAD?")

    payload = post.call_args.kwargs["json"]
    assert payload["list_sources"] is True
    assert payload["list_context"] is True
