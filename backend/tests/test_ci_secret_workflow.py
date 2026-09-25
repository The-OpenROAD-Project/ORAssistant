import json
import os
import re
import shutil
import subprocess
import textwrap
from fnmatch import fnmatch
from pathlib import Path

import pytest


WORKFLOW = Path(__file__).parents[2] / ".github/workflows/ci-secret.yaml"
WORKFLOWS_DIR = Path(__file__).parents[2] / ".github/workflows"
UPLOAD_WORKFLOW = WORKFLOWS_DIR / "upload.yml"
MAKEFILE = Path(__file__).parents[2] / "Makefile"
SECRET_TARGETS = ("backend/src", "evaluation/auto_evaluation/src")

requires_make = pytest.mark.skipif(
    shutil.which("make") is None, reason="GNU make is not installed"
)
requires_jq = pytest.mark.skipif(
    shutil.which("jq") is None, reason="jq is not installed"
)


def _run_seed_credentials(
    tmp_path: Path, secret: str
) -> subprocess.CompletedProcess[str]:
    shutil.copy(MAKEFILE, tmp_path / "Makefile")
    for target in SECRET_TARGETS:
        (tmp_path / target).mkdir(parents=True)
    return subprocess.run(
        ["make", "seed-credentials"],
        cwd=tmp_path,
        env={**os.environ, "GOOGLE_SECRET_JSON": secret},
        capture_output=True,
        text=True,
        timeout=30,
    )


@requires_make
def test_seed_credentials_writes_inline_json(tmp_path: Path) -> None:
    content = '{\n  "type": "service_account",\n  "project_id": "demo"\n}'

    result = _run_seed_credentials(tmp_path, content)

    assert result.returncode == 0, result.stderr
    for target in SECRET_TARGETS:
        written = (tmp_path / target / "secret.json").read_text()
        assert json.loads(written) == {
            "type": "service_account",
            "project_id": "demo",
        }


@requires_make
def test_seed_credentials_copies_a_file_path(tmp_path: Path) -> None:
    source = tmp_path / "creds.json"
    source.write_text('{"type": "service_account"}\n')

    result = _run_seed_credentials(tmp_path, str(source))

    assert result.returncode == 0, result.stderr
    for target in SECRET_TARGETS:
        copied = tmp_path / target / "secret.json"
        assert copied.read_text() == source.read_text()


@requires_make
def test_seed_credentials_rejects_an_empty_value(tmp_path: Path) -> None:
    result = _run_seed_credentials(tmp_path, "")

    assert result.returncode != 0
    assert "GOOGLE_SECRET_JSON is empty" in result.stderr


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


def _workflow_step_script(step_name: str, workflow: Path = WORKFLOW) -> str:
    lines = workflow.read_text().splitlines()
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


def _strings(node: object) -> list[str]:
    if isinstance(node, str):
        return [node]
    if isinstance(node, dict):
        return [
            s for key, value in node.items() for s in _strings(key) + _strings(value)
        ]
    if isinstance(node, list):
        return [s for item in node for s in _strings(item)]
    return []


def _expressions_closed(value: str) -> bool:
    """Each ${{ must be closed by }} before the next ${{ starts."""
    return all("}}" in chunk for chunk in value.split("${{")[1:])


def test_every_workflow_expression_is_closed() -> None:
    # An unquoted " #" starts a YAML comment and silently cuts a line short.
    yaml = pytest.importorskip("yaml")
    workflow = yaml.safe_load(WORKFLOW.read_text())

    unclosed = [value for value in _strings(workflow) if not _expressions_closed(value)]

    assert unclosed == []
    assert workflow["run-name"].endswith("}}")


def test_no_workflow_uses_the_gh_pat_secret() -> None:
    # The GH_PAT owner lost write access; no workflow may depend on it.
    yaml = pytest.importorskip("yaml")
    for path in sorted(WORKFLOWS_DIR.glob("*.y*ml")):
        workflow = yaml.safe_load(path.read_text())
        offenders = [s for s in _strings(workflow) if "secrets.GH_PAT" in s]
        assert offenders == [], f"{path.name}: {offenders}"


def test_commit_comment_step_uses_the_github_token() -> None:
    yaml = pytest.importorskip("yaml")
    workflow = yaml.safe_load(WORKFLOW.read_text())
    steps = [
        step
        for job in workflow["jobs"].values()
        for step in job.get("steps", [])
        if step.get("name") == "Create commit comment"
    ]

    assert len(steps) == 1
    assert steps[0]["with"]["token"] == "${{ github.token }}"


def _run_report_step(
    tmp_path: Path, needs: dict[str, object], summary: str | None
) -> tuple[subprocess.CompletedProcess[str], str]:
    """Run the PR report step with a gh stub that records its arguments."""
    calls = tmp_path / "gh_calls"
    if summary is not None:
        (tmp_path / "evaluation-output").mkdir()
        (tmp_path / "evaluation-output/llm_tests_summary.md").write_text(summary)
    stub = f'gh() {{ printf "%s\\n" "$*" >> {calls}; }}\n'
    script = stub + _workflow_step_script("Report the result on the pull request")
    result = subprocess.run(
        ["bash", "-eo", "pipefail", "-c", script],
        cwd=tmp_path,
        env={
            **os.environ,
            "NEEDS_JSON": json.dumps(needs),
            "PR": "42",
            "HEAD_SHA": "feed",
            "GITHUB_REPOSITORY": "org/repo",
            "RUN_URL": "https://example.test/run",
        },
        capture_output=True,
        text=True,
        timeout=30,
    )
    return result, calls.read_text() if calls.exists() else ""


@requires_jq
def test_report_posts_success_and_the_summary(tmp_path: Path) -> None:
    needs = {"resolve": {"result": "success"}, "docker-eval": {"result": "success"}}

    result, calls = _run_report_step(tmp_path, needs, "Aggregate Metrics\n")

    assert result.returncode == 0, result.stderr
    assert "statuses/feed -f state=success -f context=Secret CI" in calls
    assert "pr comment 42 --repo org/repo --body-file comment.md" in calls
    comment = (tmp_path / "comment.md").read_text()
    assert comment.startswith("Secret CI success: https://example.test/run")
    assert "Aggregate Metrics" in comment


@requires_jq
def test_report_posts_failure_when_an_early_job_fails(tmp_path: Path) -> None:
    needs = {
        "lint-backend": {"result": "failure"},
        "docker-eval": {"result": "skipped"},
    }

    result, calls = _run_report_step(tmp_path, needs, None)

    assert result.returncode == 0, result.stderr
    assert "state=failure" in calls
    comment = (tmp_path / "comment.md").read_text()
    assert "Secret CI failure with no evaluation output" in comment


def _run_summarize_step(tmp_path: Path, output: str | None) -> Path:
    """Run the summarize step and return the summary path it may create."""
    work = tmp_path / "evaluation/auto_evaluation"
    work.mkdir(parents=True)
    if output is not None:
        (work / "llm_tests_output.txt").write_text(output)
    result = subprocess.run(
        [
            "bash",
            "-eo",
            "pipefail",
            "-c",
            _workflow_step_script("Summarize evaluation output"),
        ],
        cwd=work,
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert result.returncode == 0, result.stderr
    return work / "llm_tests_summary.md"


def test_summary_keeps_only_the_aggregate_metrics(tmp_path: Path) -> None:
    progress = "".join(f"test case {i} details\n" * 40 for i in range(200))
    output = progress + "border\nAggregate Metrics\nPass Rate: 70.0%\n"

    summary = _run_summarize_step(tmp_path, output).read_text()

    assert len(output) > 65536
    assert len(summary) < 65536
    assert summary.startswith("```text\nborder\nAggregate Metrics")
    assert "Pass Rate: 70.0%" in summary
    assert "test case 0 details" not in summary


def test_summary_falls_back_to_the_last_lines(tmp_path: Path) -> None:
    output = "".join(f"line {i}\n" for i in range(300)) + "Traceback: boom\n"

    summary = _run_summarize_step(tmp_path, output).read_text()

    assert "Traceback: boom" in summary
    assert "line 0\n" not in summary


def test_summary_is_skipped_without_output(tmp_path: Path) -> None:
    assert not _run_summarize_step(tmp_path, None).exists()


def test_docker_eval_pins_the_corpus_revision() -> None:
    yaml = pytest.importorskip("yaml")
    workflow = yaml.safe_load(WORKFLOW.read_text())
    job = workflow["jobs"]["docker-eval"]
    step = next(s for s in job["steps"] if s.get("name") == "Download HF dataset")

    assert re.fullmatch(r"[0-9a-f]{40}", job["env"]["HF_RAG_REVISION"])
    assert '--revision "$HF_RAG_REVISION"' in step["run"]


def _run_download_step(
    tmp_path: Path, revision: str, cached: str | None
) -> tuple[subprocess.CompletedProcess[str], str]:
    """Run the dataset download step with stubbed uv and hf commands.

    cached is the revision in data/.hf_revision: None leaves data/ absent,
    and "" leaves an old corpus that has no revision file.
    """
    calls = tmp_path / "hf_calls"
    if cached is not None:
        (tmp_path / "data/markdown").mkdir(parents=True)
        (tmp_path / "data/markdown/old.md").write_text("old\n")
        if cached:
            (tmp_path / "data/.hf_revision").write_text(cached + "\n")
    stub = textwrap.dedent(
        f"""
        uv() {{ :; }}
        hf() {{
          printf '%s\\n' "$*" >> {calls}
          while [ "$#" -gt 0 ] && [ "$1" != --local-dir ]; do shift; done
          mkdir -p "$2/markdown"
          echo new > "$2/markdown/new.md"
        }}
        """
    )
    script = stub + _workflow_step_script("Download HF dataset")
    result = subprocess.run(
        ["bash", "-eo", "pipefail", "-c", script],
        cwd=tmp_path,
        env={**os.environ, "HF_RAG_REVISION": revision},
        capture_output=True,
        text=True,
        timeout=30,
    )
    return result, calls.read_text() if calls.exists() else ""


PINNED = "a" * 40


def test_download_fetches_the_pinned_revision_on_a_new_runner(
    tmp_path: Path,
) -> None:
    result, calls = _run_download_step(tmp_path, PINNED, None)

    assert result.returncode == 0, result.stderr
    assert f"--revision {PINNED} --local-dir ./data" in calls
    assert (tmp_path / "data/.hf_revision").read_text().strip() == PINNED
    assert (tmp_path / "data/markdown/new.md").exists()


def test_download_keeps_a_cache_at_the_pinned_revision(tmp_path: Path) -> None:
    result, calls = _run_download_step(tmp_path, PINNED, PINNED)

    assert result.returncode == 0, result.stderr
    assert calls == ""
    assert (tmp_path / "data/markdown/old.md").exists()


@pytest.mark.parametrize("cached", ["b" * 40, ""], ids=["other", "unknown"])
def test_download_replaces_a_cache_at_another_revision(
    tmp_path: Path, cached: str
) -> None:
    result, calls = _run_download_step(tmp_path, PINNED, cached)

    assert result.returncode == 0, result.stderr
    assert calls.count("download") == 1
    assert not (tmp_path / "data/markdown/old.md").exists()
    assert (tmp_path / "data/markdown/new.md").exists()
    assert (tmp_path / "data/.hf_revision").read_text().strip() == PINNED


def test_download_fails_without_a_revision(tmp_path: Path) -> None:
    result, calls = _run_download_step(tmp_path, "", "")

    assert result.returncode != 0
    assert calls == ""
    assert (tmp_path / "data/markdown/old.md").exists()


def _upload_workflow() -> dict:
    yaml = pytest.importorskip("yaml")
    workflow = yaml.safe_load(UPLOAD_WORKFLOW.read_text())
    # PyYAML reads the bare key "on" as True.
    workflow["on"] = workflow.pop(True)
    return workflow


def test_upload_builds_current_master_unless_commits_are_given() -> None:
    workflow = _upload_workflow()
    inputs = workflow["on"]["workflow_dispatch"]["inputs"]
    steps = workflow["jobs"]["or-manpages"]["steps"]
    build = next(s for s in steps if s.get("name") == "Build the corpus")

    assert inputs["branch"]["required"] is True
    assert inputs["or_commit"]["default"] == ""
    assert inputs["orfs_commit"]["default"] == ""
    # build_docs.py resolves an empty commit to the current master.
    assert build["env"] == {
        "OR_REPO_COMMIT": "${{ inputs.or_commit }}",
        "ORFS_REPO_COMMIT": "${{ inputs.orfs_commit }}",
    }
    assert "COMMIT" not in " ".join(workflow.get("env", {}))


def test_upload_scripts_take_inputs_through_env() -> None:
    workflow = _upload_workflow()
    scripts = [
        step["run"]
        for job in workflow["jobs"].values()
        for step in job["steps"]
        if "run" in step
    ]

    assert scripts
    assert [s for s in scripts if "${{" in s] == []


def _run_upload_script(
    tmp_path: Path, step_name: str, branch: str
) -> tuple[subprocess.CompletedProcess[str], list[list[str]]]:
    """Run an upload.yml step with stubbed hf and git commands.

    Return the result and the argument list of each hf call.
    """
    calls = tmp_path / "hf_calls"
    (tmp_path / ".venv/bin").mkdir(parents=True)
    (tmp_path / ".venv/bin/activate").touch()
    stub = textwrap.dedent(
        f"""
        hf() {{ printf '%s\\n' "$@" --- >> {calls}; }}
        git() {{ printf '%s\\trefs/heads/%s\\n' {"c" * 40} "$BRANCH"; }}
        """
    )
    script = stub + _workflow_step_script(step_name, UPLOAD_WORKFLOW)
    result = subprocess.run(
        ["bash", "-eo", "pipefail", "-c", script],
        cwd=tmp_path,
        env={
            **os.environ,
            "BRANCH": branch,
            "HF_RAG_REPO": "org/dataset",
            "GITHUB_SHA": "abc123",
            "GITHUB_STEP_SUMMARY": str(tmp_path / "summary.md"),
        },
        capture_output=True,
        text=True,
        timeout=30,
    )
    text = calls.read_text() if calls.exists() else ""
    hf_calls = [c.split("\n")[:-1] for c in text.split("---\n") if c]
    return result, hf_calls


@pytest.mark.parametrize("branch", ["", "main", "refs/heads/main"])
def test_upload_rejects_the_main_branch(tmp_path: Path, branch: str) -> None:
    result, _ = _run_upload_script(tmp_path, "Check the branch", branch)

    assert result.returncode != 0
    assert "other than main" in result.stdout


def test_upload_accepts_a_named_branch(tmp_path: Path) -> None:
    result, _ = _run_upload_script(tmp_path, "Check the branch", "corpus-2026-09")

    assert result.returncode == 0, result.stderr


def test_upload_replaces_the_corpus_on_the_branch(tmp_path: Path) -> None:
    result, hf_calls = _run_upload_script(
        tmp_path, "Upload to the Hugging Face branch", "corpus-2026-09"
    )

    assert result.returncode == 0, result.stderr
    create, upload = hf_calls
    assert create == [
        "repos", "branch", "create", "org/dataset", "corpus-2026-09",
        "--repo-type", "dataset", "--exist-ok",
    ]  # fmt: skip
    assert upload[:4] == ["upload", "org/dataset", "./data", "."]
    assert upload[upload.index("--revision") + 1] == "corpus-2026-09"
    assert upload[upload.index("--repo-type") + 1] == "dataset"
    deletes = [upload[i + 1] for i, arg in enumerate(upload) if arg == "--delete"]
    corpus = [
        "markdown/OR_docs/tools/gpl.md",
        "html/or_website/index.html",
        "pdf/OR_publications/c389.pdf",
        "source_list.json",
        "BUILD_INFO.json",
    ]
    for path in corpus:
        assert any(fnmatch(path, p) for p in deletes), path
    # The dataset card stays. Hugging Face never deletes .gitattributes.
    for path in ["README.md", "LICENSE"]:
        assert not any(fnmatch(path, p) for p in deletes), path
    assert "c" * 40 in (tmp_path / "summary.md").read_text()
