"""
Retrieval record of each case in one evaluation run.

The aggregate scores do not show which retrieval tool the backend ran or
which documents it found for a question. eval_main.py prints one line for
each case while it queries the backend:

    Case 20: tool=retrieve_cmds sources=[https://a.example,https://b.example]

It also appends the same record to CASES_FILE in its working directory, one
JSON object per line, and flushes each line. The file is complete up to the
last answered case, also when the retrieval check stops the run:

    {"index": 20, "question": "...", "tool": "retrieve_cmds", "sources": ["https://a.example", "https://b.example"]}

- index: the 0-based position of the question in the dataset, after the
  header row. The DeepEval test case for it is named test_case_<index>.
- tool: the retrieval tools that the backend reports, joined with ",".
  "unknown" if the backend reports none.
- sources: the source URL of each context source, in the backend's order.

DeepEval gets tool and sources as test case metadata.
"""

import json
from typing import Any, TextIO

CASES_FILE = "eval_cases.jsonl"
UNKNOWN = "unknown"


def record(index: int, question: str, response: dict) -> dict[str, Any]:
    """Make the record of one case from the backend response."""
    return {
        "index": index,
        "question": question,
        "tool": ",".join(response.get("tools") or []) or UNKNOWN,
        "sources": [source["source"] for source in response["context_sources"]],
    }


def format_line(case: dict[str, Any]) -> str:
    sources = ",".join(case["sources"])
    return f"Case {case['index']}: tool={case['tool']} sources=[{sources}]"


def append(file: TextIO, case: dict[str, Any]) -> None:
    """Write one record as a line and flush it, so a stopped run keeps it."""
    file.write(json.dumps(case) + "\n")
    file.flush()
