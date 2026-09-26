# Auto-evaluation

This repository houses the scripts needed for auto-evaluation.

## Retrieval check

`eval_main.py` stops with a non-zero exit before the judge runs when more than
10% of the questions (`MAX_EMPTY_RETRIEVAL_SHARE`) get no retrieval context or
the answer `invalid`. That means the backend is broken, and the scores would be
0%. The message gives the count and two example questions.

## Run metadata

Each run prints one line before the retrieval check and the DeepEval results,
and passes the same values to DeepEval as hyperparameters:

```text
Run metadata: judge=<model> backend=<provider>:<model> deepeval=<version> dataset=<commit> orassistant=<commit>
```

The dataset value is the Hugging Face commit that was downloaded, not a
branch name. A judge or dataset change can move the scores as much as a code
change, so compare scores only between runs with the same judge and dataset.
`summarize_output.sh` puts this line above the Aggregate Metrics block in the
Secret CI comment. See `run_metadata.py` for the meaning of each value.

## Results file

Each run writes `eval_results.json` to its working directory, also when the
retrieval check stops the run. It holds the schema version, the run status,
the run metadata, the test count, the empty-context count, and the mean score
and pass rate of each metric. A stopped run has `"status": "stopped"` and
`"metrics": null`. Secret CI uploads the file from master runs as the
artifact `eval-results-<run id>` and keeps it 90 days, as a baseline for later
runs. See `run_results.py` for the schema.

## Case records

Each case prints one line with the retrieval tool that the backend ran and the
source URLs that it found:

```text
Case 20: tool=retrieve_cmds sources=[https://a.example,https://b.example]
```

The index is the 0-based question position in the dataset. The DeepEval test
case is named `test_case_<index>` and has the tool and sources as metadata.
The run also writes the same records to `eval_cases.jsonl` in its working
directory, one JSON line per case, as it goes. The file is not uploaded. See
`eval_cases.py` for the format.

## Case subset

`--cases 20,84` evaluates only those 0-based question indexes, so case 84 is
"What is OpenROAD?". The cases keep their dataset indexes in their names and
records. `--skip-judge` prints the case records and stops before the
retrieval check and DeepEval. The backend still needs its Google credentials.
`llm_tests.sh` gives the arguments after the limit to `eval_main.py`:

```bash
./llm_tests.sh "" --cases 20,84 --skip-judge
```

The summary averages every case in the DeepEval cache, so run `make clean` in
`evaluation/` before a subset run. Otherwise earlier cases count too.

## Judge change

A new judge model moves the scores on its own, so later runs cannot tell a
judge change from a code change. Before a pull request changes `JUDGE_MODEL`
in `eval_main.py`, run both judges on the same commit and dataset, and post
the delta in the pull request. Run from `evaluation/`, with the backend up:

```bash
make clean
(cd auto_evaluation && uv run ./llm_tests.sh 5 --judge OLD_MODEL)
cp auto_evaluation/eval_results.json old.json
make clean
(cd auto_evaluation && uv run ./llm_tests.sh 5 --judge NEW_MODEL)
cp auto_evaluation/eval_results.json new.json
uv run python auto_evaluation/compare_results.py old.json new.json
```

`make clean` before each run is necessary, because the summary averages
every case in the DeepEval cache (see Case subset). Use a larger limit, or no limit (`""`), for
the delta that you post. `compare_results.py` exits with 1 when the two files
come from a different commit or dataset.
