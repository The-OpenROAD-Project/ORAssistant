#!/bin/bash -eu

retrievers=(
    "agent-retriever"
)

# DeepEval bounds the whole async evaluation by one per-task budget (180 s by
# default) plus a short buffer. Test cases wait behind a concurrency limit, so
# the full dataset with a slow judge model runs out of time. Keep a caller's
# value.
export DEEPEVAL_PER_TASK_TIMEOUT_SECONDS_OVERRIDE="${DEEPEVAL_PER_TASK_TIMEOUT_SECONDS_OVERRIDE:-900}"

# Set default limit (empty means run all)
LIMIT=${1:-}

echo "==================================="
echo "==> Dataset: EDA Corpus"
if [ -n "$LIMIT" ]; then
    echo "==> Running with limit: $LIMIT questions"
fi
for retriever in "${retrievers[@]}" ; do
    echo "==> Running tests for $retriever"
    if [ -n "$LIMIT" ]; then
        python eval_main.py \
           --base_url http://localhost:8000 \
           --dataset ./dataset/EDA_Corpus_100_Question.csv \
           --retriever $retriever \
           --limit $LIMIT
    else
        python eval_main.py \
           --base_url http://localhost:8000 \
           --dataset ./dataset/EDA_Corpus_100_Question.csv \
           --retriever $retriever
    fi
done
echo "==================================="
