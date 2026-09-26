"""
Tests for the gate that compares a run's scores with the last master baseline.
"""

import json
from pathlib import Path

import pytest

from auto_evaluation import baseline_gate, run_results

METADATA = {
    "judge": "gemini-judge",
    "backend": "gemini:3.6_flash",
    "deepeval": "4.2.3",
    "dataset": "abc123",
    "orassistant": "def456",
}


def _results(
    precision: float = 0.8,
    recall: float = 0.7,
    status: str = "completed",
    **metadata: str,
) -> dict:
    return {
        "schema_version": 1,
        "status": status,
        "metadata": {**METADATA, **metadata},
        "test_count": 100,
        "empty_context_count": 0,
        "metrics": None
        if status != "completed"
        else {
            "Contextual Precision": {"mean": 0.9, "pass_rate": precision},
            "Contextual Recall": {"mean": 0.8, "pass_rate": recall},
            "Hallucination": {"mean": 0.9, "pass_rate": 0.3},
        },
    }


def test_the_margin_is_five_points() -> None:
    assert baseline_gate.MARGIN == 0.05


def test_a_small_drop_passes() -> None:
    verdict = baseline_gate.compare(_results(0.76, 0.66), _results(0.8, 0.7))

    assert verdict.passed
    assert not verdict.skipped


def test_a_drop_of_exactly_the_margin_passes() -> None:
    # 0.74 - 0.79 is -0.05000000000000004 in floating point.
    verdict = baseline_gate.compare(_results(0.74), _results(0.79))

    assert verdict.passed


def test_a_precision_drop_over_the_margin_fails() -> None:
    verdict = baseline_gate.compare(_results(0.72, 0.7), _results(0.8, 0.7))

    assert not verdict.passed
    text = "\n".join(verdict.lines)
    assert "Contextual Precision pass rate: baseline 0.80, current 0.72" in text
    assert "delta -0.08" in text
    assert "FAIL" in text


def test_a_recall_drop_over_the_margin_fails() -> None:
    verdict = baseline_gate.compare(_results(0.8, 0.6), _results(0.8, 0.7))

    assert not verdict.passed
    assert any("Contextual Recall" in line and "FAIL" in line for line in verdict.lines)


def test_other_metrics_do_not_gate() -> None:
    current = _results()
    current["metrics"]["Hallucination"]["pass_rate"] = 0.0

    assert baseline_gate.compare(current, _results()).passed


@pytest.mark.parametrize("field", ["judge", "dataset"])
def test_a_different_judge_or_dataset_skips(field: str) -> None:
    verdict = baseline_gate.compare(
        _results(0.1, 0.1), _results(0.8, 0.7, **{field: "other"})
    )

    assert verdict.passed
    assert verdict.skipped
    assert any(field in line and "other" in line for line in verdict.lines)


def test_no_baseline_skips() -> None:
    verdict = baseline_gate.compare(_results(), None)

    assert verdict.passed
    assert verdict.skipped


@pytest.mark.parametrize(
    ("current", "baseline"),
    [
        (_results(status="stopped"), _results()),
        (_results(), _results(status="stopped")),
    ],
)
def test_a_run_without_scores_skips(current: dict, baseline: dict) -> None:
    verdict = baseline_gate.compare(current, baseline)

    assert verdict.passed
    assert verdict.skipped


def test_the_gate_reads_the_schema_that_runs_write() -> None:
    assert baseline_gate.SCHEMA_VERSION == run_results.SCHEMA_VERSION


def test_another_schema_version_skips() -> None:
    baseline = {**_results(0.8), "schema_version": 2}

    verdict = baseline_gate.compare(_results(0.1), baseline)

    assert verdict.passed
    assert verdict.skipped
    assert "schema version 2" in verdict.lines[0]


def test_a_missing_metric_is_skipped_but_others_still_gate() -> None:
    baseline = _results(0.8, 0.7)
    del baseline["metrics"]["Contextual Recall"]

    verdict = baseline_gate.compare(_results(0.7, 0.1), baseline)

    assert not verdict.passed
    assert any(
        "Contextual Recall" in line and "skipped" in line for line in verdict.lines
    )


def _write(path: Path, results: dict) -> str:
    path.write_text(json.dumps(results))
    return str(path)


def test_main_returns_1_and_prints_the_deltas_on_a_drop(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    current = _write(tmp_path / "current.json", _results(0.7))
    baseline = _write(tmp_path / "baseline.json", _results(0.8))

    assert baseline_gate.main(["--current", current, "--baseline", baseline]) == 1
    out = capsys.readouterr().out
    assert "::error::" in out
    assert "baseline 0.80, current 0.70, delta -0.10" in out


def test_main_passes_without_a_baseline_file(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    current = _write(tmp_path / "current.json", _results())

    assert baseline_gate.main(["--current", current]) == 0
    assert "::notice::" in capsys.readouterr().out
