import os
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path


SCRIPT = Path(__file__).parents[1] / "auto_evaluation/llm_tests.sh"
MAKEFILE = Path(__file__).parents[1] / "Makefile"
TIMEOUT_VAR = "DEEPEVAL_PER_TASK_TIMEOUT_SECONDS_OVERRIDE"
BUFFER_VAR = "DEEPEVAL_TASK_GATHER_BUFFER_SECONDS_OVERRIDE"


def _budget_seen_by_python(env: dict[str, str]) -> set[str]:
    """Run the script with python stubbed by an exported bash function."""
    # A function, not a stub file, so a noexec temporary directory still works.
    wrapper = (
        f'python() {{ echo "budget=${{{TIMEOUT_VAR}}} buffer=${{{BUFFER_VAR}}}"; }}\n'
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


def _args_seen_through_make(*make_args: str) -> list[str]:
    """Run `make llm-tests` with uv and python stubbed, and return the eval args."""
    with tempfile.TemporaryDirectory() as tmp:
        work = Path(tmp)
        shutil.copy(MAKEFILE, work / "Makefile")
        (work / "auto_evaluation").mkdir()
        shutil.copy(SCRIPT, work / "auto_evaluation/llm_tests.sh")
        # Each non-interactive bash reads BASH_ENV, so the recipe's bash and the
        # script both get the stubs. Run the script with bash, so that a noexec
        # temporary directory still works.
        stubs = work / "stubs.sh"
        stubs.write_text(
            'uv() { [ "$1" = run ] || return 1; shift; bash "$@"; }\n'
            'python() { printf "arg=%s\\n" "$@"; }\n'
        )
        result = subprocess.run(
            ["make", "-s", "llm-tests", *make_args],
            cwd=work,
            env={**os.environ, "BASH_ENV": str(stubs)},
            capture_output=True,
            text=True,
            timeout=30,
        )
    if result.returncode != 0:
        raise AssertionError(result.stdout + result.stderr)
    prefix = "arg="
    return [
        line[len(prefix) :]
        for line in result.stdout.splitlines()
        if line.startswith(prefix)
    ]


class LlmTestsScriptTest(unittest.TestCase):
    def test_script_raises_the_deepeval_budget(self) -> None:
        env = {
            k: v for k, v in os.environ.items() if k not in {TIMEOUT_VAR, BUFFER_VAR}
        }

        self.assertEqual(_budget_seen_by_python(env), {"budget=900 buffer=2700"})

    def test_script_keeps_a_caller_budget(self) -> None:
        env = {**os.environ, TIMEOUT_VAR: "1234", BUFFER_VAR: "5678"}

        self.assertEqual(_budget_seen_by_python(env), {"budget=1234 buffer=5678"})

    def test_script_passes_the_limit(self) -> None:
        args = _args_seen_by_python("5")

        self.assertEqual(args[-2:], ["--limit", "5"])

    def test_script_passes_later_arguments_to_the_eval(self) -> None:
        args = _args_seen_by_python("", "--cases", "20,84", "--skip-judge")

        self.assertNotIn("--limit", args)
        self.assertEqual(args[-3:], ["--cases", "20,84", "--skip-judge"])


@unittest.skipIf(shutil.which("make") is None, "make is not installed")
class LlmTestsMakeTargetTest(unittest.TestCase):
    def test_make_runs_every_case_with_the_default_judge(self) -> None:
        args = _args_seen_through_make()

        self.assertIn("--retriever", args)
        self.assertNotIn("--limit", args)
        self.assertNotIn("--cases", args)
        self.assertNotIn("--judge", args)

    def test_make_passes_eval_args_to_the_eval(self) -> None:
        args = _args_seen_through_make("EVAL_ARGS=--judge other-judge --limit 5")

        self.assertEqual(args[-4:], ["--judge", "other-judge", "--limit", "5"])


if __name__ == "__main__":
    unittest.main()
