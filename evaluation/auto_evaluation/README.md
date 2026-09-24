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
