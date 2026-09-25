"""
Tests for the results file that each evaluation run writes for Secret CI.
"""

import json
from typing import Any
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from deepeval.models.base_model import DeepEvalBaseLLM

from auto_evaluation import run_results
from auto_evaluation.eval_main import EmptyRetrievalError, EvaluationHarness

METADATA = {
    "judge": "gemini-judge",
    "backend": "gemini:3.6_flash",
    "deepeval": "4.2.3",
    "dataset": "abc123",
    "orassistant": "def456",
}


def _answer(context: list[str], response: str = "ok") -> dict:
    return {
        "response": response,
        "context_sources": [{"source": "doc", "context": c} for c in context],
    }


def _evaluate(answers: list[dict]) -> None:
    """Run the harness with the judge stubbed and the given backend answers."""
    harness = object.__new__(EvaluationHarness)
    harness.eval_model = MagicMock(spec=DeepEvalBaseLLM)
    harness.qns = [
        {"question": f"q{i}", "ground_truth": "a"} for i in range(len(answers))
    ]
    with (
        patch.object(harness, "query", side_effect=[(a, 1.0) for a in answers]),
        patch("auto_evaluation.eval_main.evaluate"),
    ):
        harness.evaluate("agent-retriever", metadata=METADATA)


def _write_deepeval_cache(directory: Path, cases: list[dict[str, tuple]]) -> None:
    """Write the cache that DeepEval's evaluate() leaves for read_deepeval_cache."""
    lookup = {
        f"case-{i}": {
            "cached_metrics_data": [
                {"metric_data": {"name": name, "score": score, "success": success}}
                for name, (score, success) in case.items()
            ]
        }
        for i, case in enumerate(cases)
    }
    (directory / ".deepeval").mkdir()
    (directory / ".deepeval/.deepeval-cache.json").write_text(
        json.dumps({"test_cases_lookup_map": lookup})
    )


def _read_results(directory: Path) -> Any:
    return json.loads((directory / run_results.RESULTS_FILE).read_text())


def test_completed_run_writes_metrics_counts_and_metadata(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    _write_deepeval_cache(
        tmp_path,
        [
            {
                "Contextual Precision": (1.0, True),
                "Contextual Recall": (0.25, False),
                "Hallucination": (1.0, True),
            },
            {
                "Contextual Precision": (0.5, False),
                "Contextual Recall": (0.25, False),
                "Hallucination": (0.5, True),
            },
        ],
    )

    # One of ten answers is empty: below the retrieval limit, so the judge runs.
    _evaluate([_answer(["ctx"])] * 9 + [_answer([])])

    assert _read_results(tmp_path) == {
        "schema_version": 1,
        "status": "completed",
        "metadata": METADATA,
        "test_count": 10,
        "empty_context_count": 1,
        "metrics": {
            "Contextual Precision": {"mean": 0.75, "pass_rate": 0.5},
            "Contextual Recall": {"mean": 0.25, "pass_rate": 0.0},
            "Hallucination": {"mean": 0.75, "pass_rate": 1.0},
        },
    }


def test_stopped_run_writes_null_metrics(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)

    with pytest.raises(EmptyRetrievalError):
        _evaluate([_answer(["ctx"])] * 3 + [_answer([], response="invalid")] * 2)

    assert _read_results(tmp_path) == {
        "schema_version": 1,
        "status": "stopped",
        "metadata": METADATA,
        "test_count": 5,
        "empty_context_count": 2,
        "metrics": None,
    }
