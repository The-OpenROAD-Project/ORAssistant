"""
Run metadata recorded with each evaluation result.

A judge or dataset change can move the scores as much as a code change, so
each run names what produced its scores. The eval passes these values to
DeepEval as hyperparameters and prints them as one line:

    Run metadata: judge=<model> backend=<provider>:<model> deepeval=<version> dataset=<commit> orassistant=<commit>

- judge: the DeepEval judge model.
- backend: LLM_MODEL and its model setting (GOOGLE_GEMINI or OLLAMA_MODEL)
  from the eval environment. CI copies the same backend .env to the eval.
- deepeval: the installed DeepEval version.
- dataset: the Hugging Face commit of the eval dataset.
- orassistant: the git commit of the ORAssistant checkout.

Keys keep this order, and values contain no spaces. A value that cannot be
found is "unknown". Tools read the last line that starts with PREFIX.
"""

import os
import subprocess
from importlib.metadata import version

PREFIX = "Run metadata:"
UNKNOWN = "unknown"

# The environment variable that names the model for each LLM_MODEL provider.
_BACKEND_MODEL_VARS = {"gemini": "GOOGLE_GEMINI", "ollama": "OLLAMA_MODEL"}


def collect(judge_model: str, dataset_revision: str) -> dict[str, str]:
    return {
        "judge": judge_model,
        "backend": _backend_model(),
        "deepeval": version("deepeval"),
        "dataset": dataset_revision,
        "orassistant": _orassistant_commit(),
    }


def format_line(metadata: dict[str, str]) -> str:
    values = " ".join(f"{key}={value}" for key, value in metadata.items())
    return f"{PREFIX} {values}"


def _backend_model() -> str:
    provider = os.getenv("LLM_MODEL", "")
    model = os.getenv(_BACKEND_MODEL_VARS.get(provider, ""), "")
    return f"{provider}:{model}" if model else UNKNOWN


def _orassistant_commit() -> str:
    try:
        result = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=os.path.dirname(os.path.abspath(__file__)),
            capture_output=True,
            text=True,
            check=True,
        )
    except (OSError, subprocess.CalledProcessError):
        return UNKNOWN
    return result.stdout.strip()
