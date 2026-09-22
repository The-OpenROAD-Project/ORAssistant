import subprocess
import textwrap
from pathlib import Path


WORKFLOW = Path(__file__).parents[2] / ".github/workflows/ci-secret.yaml"


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
