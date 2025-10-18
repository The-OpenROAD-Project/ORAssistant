#!/bin/bash -eu

retrievers=(
    "agent-retriever"
)

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
