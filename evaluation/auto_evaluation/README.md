# Auto-evaluation

This repository houses the scripts needed for auto-evaluation.

## Retrieval check

`eval_main.py` stops with a non-zero exit before the judge runs when more than
10% of the questions (`MAX_EMPTY_RETRIEVAL_SHARE`) get no retrieval context or
the answer `invalid`. That means the backend is broken, and the scores would be
0%. The message gives the count and two example questions.
