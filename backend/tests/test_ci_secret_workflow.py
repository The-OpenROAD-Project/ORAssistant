import json
import os
import shutil
import subprocess
import textwrap
from pathlib import Path

import pytest


WORKFLOW = Path(__file__).parents[2] / ".github/workflows/ci-secret.yaml"

requires_jq = pytest.mark.skipif(
    shutil.which("jq") is None, reason="jq is not installed"
)


def _run_resolve_step(
    tmp_path: Path, pr: str, pr_json: dict[str, object] | None
) -> tuple[subprocess.CompletedProcess[str], dict[str, str]]:
    """Run the resolve step with a stubbed gh CLI and return its outputs."""
    output_file = tmp_path / "github_output"
    output_file.touch()
    stub = textwrap.dedent(
        f"""
        gh() {{
          case "$*" in
            *"/pulls/"*) printf '%s' {json.dumps(json.dumps(pr_json or {}))} ;;
            *"/statuses/"*) echo "status: $*" ;;
            *) echo "unexpected gh call: $*" >&2; return 1 ;;
          esac
        }}
        sleep() {{ :; }}
        """
    )
    script = stub + _workflow_step_script("Resolve the code under test")
    result = subprocess.run(
        ["bash", "-eo", "pipefail", "-c", script],
        env={
            **os.environ,
            "PR": pr,
            "GITHUB_SHA": "abc123",
            "GITHUB_REPOSITORY": "org/repo",
            "GITHUB_OUTPUT": str(output_file),
            "RUN_URL": "https://example.test/run",
        },
        capture_output=True,
        text=True,
        timeout=30,
    )
    outputs = dict(
        line.split("=", 1)
        for line in output_file.read_text().splitlines()
        if "=" in line
    )
    return result, outputs


@requires_jq
def test_resolve_uses_the_pushed_commit_without_a_pr(tmp_path: Path) -> None:
    result, outputs = _run_resolve_step(tmp_path, "", None)

    assert result.returncode == 0, result.stderr
    assert outputs == {"ref": "abc123", "pr": "", "head_sha": ""}


@requires_jq
def test_resolve_targets_the_pr_merge_ref(tmp_path: Path) -> None:
    pr_json = {"state": "open", "mergeable": True, "head": {"sha": "feed"}}

    result, outputs = _run_resolve_step(tmp_path, "42", pr_json)

    assert result.returncode == 0, result.stderr
    assert outputs == {"ref": "refs/pull/42/merge", "pr": "42", "head_sha": "feed"}
    assert "statuses/feed" in result.stdout
    assert "state=pending" in result.stdout


@requires_jq
def test_resolve_rejects_a_closed_pr(tmp_path: Path) -> None:
    pr_json = {"state": "closed", "mergeable": False, "head": {"sha": "feed"}}

    result, outputs = _run_resolve_step(tmp_path, "42", pr_json)

    assert result.returncode != 0
    assert "not open" in result.stdout
    assert outputs == {}


@requires_jq
def test_resolve_rejects_a_conflicting_pr(tmp_path: Path) -> None:
    pr_json = {"state": "open", "mergeable": False, "head": {"sha": "feed"}}

    result, outputs = _run_resolve_step(tmp_path, "42", pr_json)

    assert result.returncode != 0
    assert "not mergeable" in result.stdout
    assert outputs == {}


def _workflow_step_script(step_name: str) -> str:
    lines = WORKFLOW.read_text().splitlines()
    step_index = next(
        index
        for index, line in enumerate(lines)
        if line.strip() == f"- name: {step_name}"
    )
    run_index = next(
        index
        for index in range(step_index + 1, len(lines))
        if lines[index].strip() == "run: |"
    )
    block_indent = len(lines[run_index]) - len(lines[run_index].lstrip()) + 2
    block = []
    for line in lines[run_index + 1 :]:
        indent = len(line) - len(line.lstrip())
        if line.strip() and indent < block_indent:
            break
        block.append(line)
    return textwrap.dedent("\n".join(block))


def test_graph_readiness_timeout_fails_the_step() -> None:
    script = "curl() { return 22; }\nsleep() { :; }\n"
    script += _workflow_step_script("Wait for graph readiness")
    result = subprocess.run(
        ["bash", "-eo", "pipefail", "-c", script],
        capture_output=True,
        text=True,
        timeout=10,
    )

    assert result.returncode != 0
    assert "Graph did not become ready" in result.stdout
