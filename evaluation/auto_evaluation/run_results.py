"""
Machine-readable result of one evaluation run.

eval_main.py writes RESULTS_FILE to its working directory at the end of a
run, and also when the retrieval check stops the run. Secret CI uploads it
from master runs as the artifact eval-results-<run id> and keeps it 90 days,
so a later run can compare its scores with a master baseline.

Schema version 1:

    {
      "schema_version": 1,
      "status": "completed",
      "metadata": {
        "judge": "gemini-3.1-pro-preview",
        "backend": "gemini:3.6_flash",
        "deepeval": "4.2.3",
        "dataset": "<Hugging Face commit>",
        "orassistant": "<git commit>"
      },
      "test_count": 100,
      "empty_context_count": 2,
      "metrics": {
        "Contextual Precision": {"mean": 0.81, "pass_rate": 0.78},
        "Contextual Recall": {"mean": 0.74, "pass_rate": 0.69},
        "Hallucination": {"mean": 0.93, "pass_rate": 0.9}
      }
    }

- schema_version: increases when a field changes meaning or goes away.
- status: "completed", or "stopped" when the retrieval check stopped the run
  before the judge ran. A stopped run has "metrics": null.
- metadata: the run_metadata.collect() values. Compare scores only between
  runs with the same judge and dataset.
- test_count: the number of questions sent to the backend.
- empty_context_count: the answers with no retrieval context or the answer
  "invalid", as the retrieval check counts them.
- metrics: for each DeepEval metric name, the mean score and the pass rate.
  Both are fractions from 0 to 1, so 5 percentage points is 0.05. The object
  is empty if DeepEval left no cache.

A baseline reader skips a run whose status is not "completed" or that has no
value for the metric it compares.
"""

import json

SCHEMA_VERSION = 1
RESULTS_FILE = "eval_results.json"


def write(
    path: str,
    metadata: dict[str, str],
    test_count: int,
    empty_context_count: int,
    metrics: dict[str, dict[str, float]] | None,
) -> None:
    """Write the results file. metrics is None when the run stopped early."""
    results = {
        "schema_version": SCHEMA_VERSION,
        "status": "stopped" if metrics is None else "completed",
        "metadata": metadata,
        "test_count": test_count,
        "empty_context_count": empty_context_count,
        "metrics": metrics,
    }
    with open(path, "w") as f:
        json.dump(results, f, indent=2)
        f.write("\n")
