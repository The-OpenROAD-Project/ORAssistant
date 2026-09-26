"""
Unit tests for the DeepEval cache summary in the dataset preprocess module.
The fixture follows the DeepEval 4 cache format that evaluate() writes to
.deepeval/.deepeval-cache.json.
"""

import json

import pytest

from auto_evaluation.dataset import preprocess


def _metric(name: str, score: float, success: bool) -> dict:
    return {
        "metric_data": {
            "name": name,
            "threshold": 0.7,
            "success": success,
            "score": score,
            "strictMode": False,
            "evaluationModel": "judge",
            "evaluationCost": 0,
        },
        "metric_configuration": {
            "threshold": 0.7,
            "evaluation_model": "judge",
            "strict_mode": False,
            "include_reason": True,
        },
    }


# Three cases. Hallucination scores 1.0, 0.5 and 0.0 give a mean of 0.5 but a
# pass rate of 1/3, so the two values cannot be mixed up.
CASES = [
    [
        _metric("Contextual Precision", 1.0, True),
        _metric("Contextual Recall", 0.9, True),
        _metric("Hallucination", 1.0, True),
    ],
    [
        _metric("Contextual Precision", 0.8, True),
        _metric("Contextual Recall", 0.6, False),
        _metric("Hallucination", 0.5, False),
    ],
    [
        _metric("Contextual Precision", 0.0, False),
        _metric("Contextual Recall", 0.3, False),
        _metric("Hallucination", 0.0, False),
    ],
]


@pytest.fixture
def cache_dir(tmp_path, monkeypatch):
    lookup = {f"case-{i}": {"cached_metrics_data": m} for i, m in enumerate(CASES)}
    (tmp_path / ".deepeval").mkdir()
    (tmp_path / ".deepeval" / ".deepeval-cache.json").write_text(
        json.dumps({"test_cases_lookup_map": lookup})
    )
    monkeypatch.chdir(tmp_path)
    return tmp_path


def _summary_value(output: str, section: str, metric: str) -> float:
    lines = output.splitlines()
    start = lines.index(section)
    for line in lines[start + 1 :]:
        if line.startswith(metric + " "):
            return float(line[len(metric) + 1 :].split()[0])
    raise AssertionError(f"{metric} not found under {section!r}:\n{output}")


def test_average_scores_are_the_mean_of_cached_case_scores(cache_dir, capsys):
    preprocess.read_deepeval_cache()
    out = capsys.readouterr().out

    averages = "Average Metric Scores: "
    assert _summary_value(out, averages, "Contextual Precision") == pytest.approx(0.6)
    assert _summary_value(out, averages, "Contextual Recall") == pytest.approx(0.6)
    assert _summary_value(out, averages, "Hallucination") == pytest.approx(0.5)


def test_pass_rates_count_cached_successes(cache_dir, capsys):
    preprocess.read_deepeval_cache()
    out = capsys.readouterr().out

    passrates = "Metric Passrates: "
    assert _summary_value(out, passrates, "Contextual Precision") == pytest.approx(
        2 / 3
    )
    assert _summary_value(out, passrates, "Contextual Recall") == pytest.approx(1 / 3)
    assert _summary_value(out, passrates, "Hallucination") == pytest.approx(1 / 3)


def test_hallucination_average_states_its_scale(cache_dir, capsys):
    # DeepEval 3 scored the share of contradicted contexts (lower is better).
    # DeepEval 4 scores the share that is not contradicted (higher is better),
    # so the summary line must say which one it prints.
    preprocess.read_deepeval_cache()
    out = capsys.readouterr().out

    lines = out.splitlines()
    start = lines.index("Average Metric Scores: ")
    line = next(x for x in lines[start + 1 :] if x.startswith("Hallucination "))
    assert "not contradicted" in line
    assert "higher is better" in line
