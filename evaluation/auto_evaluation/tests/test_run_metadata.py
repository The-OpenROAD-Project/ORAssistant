"""
Tests for the run metadata that each evaluation run records and posts.
"""

import re
import shutil
import subprocess
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import deepeval
import pytest
from deepeval.models.base_model import DeepEvalBaseLLM

from auto_evaluation import run_metadata
from auto_evaluation.eval_main import EvaluationHarness
from auto_evaluation.dataset import hf_pull

DATASET_COMMIT = "0123456789abcdef0123456789abcdef01234567"
SUMMARIZE = Path(__file__).parents[1] / "summarize_output.sh"


class TestDatasetRevision:
    @patch("auto_evaluation.dataset.hf_pull.snapshot_download")
    @patch("auto_evaluation.dataset.hf_pull.HfApi")
    def test_pull_returns_and_downloads_the_resolved_commit(
        self, hf_api, snapshot_download
    ):
        hf_api.return_value.dataset_info.return_value = SimpleNamespace(
            sha=DATASET_COMMIT
        )

        revision = hf_pull.main()

        assert revision == DATASET_COMMIT
        assert snapshot_download.call_args.kwargs["revision"] == DATASET_COMMIT


class TestCollect:
    def test_collect_names_every_value(self, monkeypatch):
        monkeypatch.setenv("LLM_MODEL", "gemini")
        monkeypatch.setenv("GOOGLE_GEMINI", "3.6_flash")

        metadata = run_metadata.collect("gemini-judge", DATASET_COMMIT)

        assert metadata["judge"] == "gemini-judge"
        assert metadata["backend"] == "gemini:3.6_flash"
        assert metadata["deepeval"] == deepeval.__version__
        assert metadata["dataset"] == DATASET_COMMIT
        assert list(metadata) == [
            "judge",
            "backend",
            "deepeval",
            "dataset",
            "orassistant",
        ]

    @pytest.mark.skipif(shutil.which("git") is None, reason="needs git")
    def test_orassistant_is_the_checked_out_commit(self):
        head = subprocess.run(
            ["git", "log", "-1", "--format=%H"],
            cwd=Path(__file__).parent,
            capture_output=True,
            text=True,
            check=True,
        ).stdout.strip()

        metadata = run_metadata.collect("judge", DATASET_COMMIT)

        assert re.fullmatch(r"[0-9a-f]{40}", metadata["orassistant"])
        assert metadata["orassistant"] == head

    def test_backend_names_the_ollama_model(self, monkeypatch):
        monkeypatch.setenv("LLM_MODEL", "ollama")
        monkeypatch.setenv("OLLAMA_MODEL", "llama3")

        assert run_metadata.collect("judge", DATASET_COMMIT)["backend"] == (
            "ollama:llama3"
        )

    @pytest.mark.parametrize("provider", ["", "gemini"])
    def test_backend_is_unknown_without_a_model(self, monkeypatch, provider):
        monkeypatch.setenv("LLM_MODEL", provider)
        monkeypatch.delenv("GOOGLE_GEMINI", raising=False)

        assert run_metadata.collect("judge", DATASET_COMMIT)["backend"] == "unknown"


class TestFormatLine:
    def test_line_lists_values_in_order(self):
        metadata = {
            "judge": "gemini-3.1-pro-preview",
            "backend": "gemini:3.6_flash",
            "deepeval": "4.2.3",
            "dataset": "abc123",
            "orassistant": "def456",
        }

        assert run_metadata.format_line(metadata) == (
            "Run metadata: judge=gemini-3.1-pro-preview backend=gemini:3.6_flash "
            "deepeval=4.2.3 dataset=abc123 orassistant=def456"
        )


class TestEvaluationRun:
    @patch("auto_evaluation.eval_main.preprocess.read_deepeval_cache")
    @patch("auto_evaluation.eval_main.evaluate")
    def test_run_logs_metadata_as_hyperparameters(
        self, deepeval_evaluate, read_cache, capsys, tmp_path, monkeypatch
    ):
        # The run writes its results file to the working directory.
        monkeypatch.chdir(tmp_path)
        read_cache.return_value = {}
        harness = object.__new__(EvaluationHarness)
        harness.eval_model = MagicMock(spec=DeepEvalBaseLLM)
        harness.qns = [{"question": "q", "ground_truth": "a"}]
        harness.query = MagicMock(
            return_value=(
                {"response": "r", "context_sources": [{"context": "c"}]},
                1.0,
            )
        )
        metadata = {"judge": "gemini-judge", "dataset": DATASET_COMMIT}

        harness.evaluate("agent-retriever", metadata=metadata)

        assert deepeval_evaluate.call_args.kwargs["hyperparameters"] == metadata
        assert (
            f"Run metadata: judge=gemini-judge dataset={DATASET_COMMIT}"
            in capsys.readouterr().out.splitlines()
        )


def _summarize(tmp_path: Path, output: str) -> str:
    (tmp_path / "out.txt").write_text(output)
    subprocess.run(
        ["bash", str(SUMMARIZE), "out.txt", "summary.md"],
        cwd=tmp_path,
        check=True,
        timeout=30,
    )
    return (tmp_path / "summary.md").read_text()


class TestCiSummary:
    def test_metadata_line_is_above_aggregate_metrics(self, tmp_path):
        output = (
            "Evaluating: 100%\n"
            "Run metadata: judge=j backend=b deepeval=d dataset=h orassistant=c\n"
            "per-test-case results\n"
            "+---------+\n"
            "Aggregate Metrics\n"
            "Contextual Recall 0.5\n"
        )

        assert _summarize(tmp_path, output) == (
            "```text\n"
            "Run metadata: judge=j backend=b deepeval=d dataset=h orassistant=c\n"
            "+---------+\n"
            "Aggregate Metrics\n"
            "Contextual Recall 0.5\n"
            "```\n"
        )

    def test_summary_without_metadata_keeps_the_aggregate_block(self, tmp_path):
        output = "noise\n+---------+\nAggregate Metrics\nContextual Recall 0.5\n"

        assert _summarize(tmp_path, output) == (
            "```text\n+---------+\nAggregate Metrics\nContextual Recall 0.5\n```\n"
        )
