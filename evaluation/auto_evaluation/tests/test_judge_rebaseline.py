"""
Tests for running the evaluation with a chosen judge and comparing two judges.
"""

import json
from pathlib import Path
from unittest.mock import patch

import pytest

from auto_evaluation import compare_results
from auto_evaluation.eval_main import JUDGE_MODEL, EvaluationHarness, build_parser

METADATA = {
    "judge": "old-judge",
    "backend": "gemini:3.6_flash",
    "deepeval": "4.2.3",
    "dataset": "abc123",
    "orassistant": "def456",
}


def test_the_judge_defaults_to_the_current_model() -> None:
    assert build_parser().parse_args([]).judge == JUDGE_MODEL


def test_the_judge_can_be_chosen() -> None:
    assert build_parser().parse_args(["--judge", "other"]).judge == "other"


def test_the_harness_scores_with_the_chosen_judge(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.chdir(tmp_path)
    with (
        patch("auto_evaluation.eval_main.preprocess.read_data", return_value=[]),
        patch("auto_evaluation.eval_main.GoogleGeminiLangChain") as model,
        patch.object(EvaluationHarness, "sanity_check"),
    ):
        EvaluationHarness("http://backend", "data.csv", judge_model="other")

    model.assert_called_once_with(model_name="other")


def _results(judge: str, precision: float, **metadata: str) -> dict:
    return {
        "schema_version": 1,
        "status": "completed",
        "metadata": {**METADATA, "judge": judge, **metadata},
        "test_count": 5,
        "empty_context_count": 0,
        "metrics": {
            "Contextual Precision": {"mean": precision, "pass_rate": precision},
            "Contextual Recall": {"mean": 0.7, "pass_rate": 0.6},
        },
    }


def test_compare_prints_the_delta_of_each_metric() -> None:
    lines, same_run = compare_results.compare(
        _results("old-judge", 0.8), _results("new-judge", 0.6)
    )

    text = "\n".join(lines)
    assert same_run
    assert "Judge: old-judge -> new-judge" in text
    assert (
        "Contextual Precision: mean 0.80 -> 0.60 (-0.20), "
        "pass rate 0.80 -> 0.60 (-0.20)"
    ) in text
    assert "Contextual Recall: mean 0.70 -> 0.70 (+0.00)" in text


@pytest.mark.parametrize("field", ["orassistant", "dataset"])
def test_compare_flags_runs_on_different_commits(field: str) -> None:
    lines, same_run = compare_results.compare(
        _results("old-judge", 0.8), _results("new-judge", 0.8, **{field: "other"})
    )

    assert not same_run
    assert any(field in line for line in lines)


def test_compare_marks_a_metric_missing_in_one_run() -> None:
    new = _results("new-judge", 0.8)
    del new["metrics"]["Contextual Recall"]

    lines, _ = compare_results.compare(_results("old-judge", 0.8), new)

    assert "Contextual Recall: missing in one run" in lines


def test_compare_rejects_a_run_without_scores() -> None:
    stopped = {**_results("new-judge", 0.8), "status": "stopped", "metrics": None}

    with pytest.raises(ValueError, match="no scores"):
        compare_results.compare(_results("old-judge", 0.8), stopped)


def test_main_fails_when_the_runs_are_on_different_commits(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    old = tmp_path / "old.json"
    new = tmp_path / "new.json"
    old.write_text(json.dumps(_results("old-judge", 0.8)))
    new.write_text(json.dumps(_results("new-judge", 0.7, orassistant="other")))

    assert compare_results.main([str(old), str(new)]) == 1
    assert "mean 0.80 -> 0.70" in capsys.readouterr().out
