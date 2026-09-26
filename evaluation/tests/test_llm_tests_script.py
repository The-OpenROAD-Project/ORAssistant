import os
import subprocess
import unittest
from pathlib import Path


SCRIPT = Path(__file__).parents[1] / "auto_evaluation/llm_tests.sh"
TIMEOUT_VAR = "DEEPEVAL_PER_TASK_TIMEOUT_SECONDS_OVERRIDE"


def _budget_seen_by_python(env: dict[str, str]) -> set[str]:
    """Run the script with python stubbed by an exported bash function."""
    # A function, not a stub file, so a noexec temporary directory still works.
    wrapper = (
        f'python() {{ echo "budget=${{{TIMEOUT_VAR}}}"; }}\n'
        f'export -f python\nbash "{SCRIPT}"\n'
    )
    result = subprocess.run(
        ["bash", "-c", wrapper],
        env=env,
        capture_output=True,
        text=True,
        timeout=30,
    )
    if result.returncode != 0:
        raise AssertionError(result.stderr)
    return {line for line in result.stdout.splitlines() if line.startswith("budget=")}


def _args_seen_by_python(*script_args: str) -> list[str]:
    """Run the script with python stubbed, and return the eval_main.py args."""
    wrapper = (
        'python() { printf "arg=%s\\n" "$@"; }\nexport -f python\nbash "$0" "$@"\n'
    )
    result = subprocess.run(
        ["bash", "-c", wrapper, str(SCRIPT), *script_args],
        capture_output=True,
        text=True,
        timeout=30,
    )
    if result.returncode != 0:
        raise AssertionError(result.stderr)
    prefix = "arg="
    return [
        line[len(prefix) :]
        for line in result.stdout.splitlines()
        if line.startswith(prefix)
    ]


class LlmTestsScriptTest(unittest.TestCase):
    def test_script_raises_the_deepeval_budget(self) -> None:
        env = {k: v for k, v in os.environ.items() if k != TIMEOUT_VAR}

        self.assertEqual(_budget_seen_by_python(env), {"budget=900"})

    def test_script_keeps_a_caller_budget(self) -> None:
        env = {**os.environ, TIMEOUT_VAR: "1234"}

        self.assertEqual(_budget_seen_by_python(env), {"budget=1234"})

    def test_script_passes_the_limit(self) -> None:
        args = _args_seen_by_python("5")

        self.assertEqual(args[-2:], ["--limit", "5"])

    def test_script_passes_later_arguments_to_the_eval(self) -> None:
        args = _args_seen_by_python("", "--cases", "20,84", "--skip-judge")

        self.assertNotIn("--limit", args)
        self.assertEqual(args[-3:], ["--cases", "20,84", "--skip-judge"])


if __name__ == "__main__":
    unittest.main()
