#!/bin/bash -eu

retrievers=(
    "agent-retriever"
)

# DeepEval gives each active case this budget and bounds the whole batch by
# the same budget plus a buffer. Queue time counts against the batch limit.
# Keep a caller's value.
export DEEPEVAL_PER_TASK_TIMEOUT_SECONDS_OVERRIDE="${DEEPEVAL_PER_TASK_TIMEOUT_SECONDS_OVERRIDE:-900}"

# Usage: llm_tests.sh [LIMIT] [EVAL_MAIN_ARGS...]
# An empty LIMIT runs all questions. Later arguments go to eval_main.py, for
# example: llm_tests.sh "" --cases 20,84 --skip-judge
LIMIT=${1:-}
if [ $# -gt 0 ]; then
    shift
fi
if [ -n "$LIMIT" ]; then
    set -- --limit "$LIMIT" "$@"
fi

echo "==================================="
echo "==> Dataset: EDA Corpus"
if [ -n "$LIMIT" ]; then
    echo "==> Running with limit: $LIMIT questions"
fi
for retriever in "${retrievers[@]}" ; do
    echo "==> Running tests for $retriever"
    python eval_main.py \
       --base_url http://localhost:8000 \
       --dataset ./dataset/EDA_Corpus_100_Question.csv \
       --retriever $retriever \
       "$@"
done
echo "==================================="
