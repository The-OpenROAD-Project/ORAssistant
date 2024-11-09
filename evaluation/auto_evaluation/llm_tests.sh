#!/bin/bash -eu

retrievers=(
    "agent-retriever" \
    "ensemble" \
)

echo "==================================="
echo "==> Dataset: EDA Corpus"
for retriever in "${retrievers[@]}" ; do
    echo "==> Running tests for $retriever"
    python auto_evaluation/eval_main.py \
       --base_url http://localhost:8000 \
       --dataset ./auto_evaluation/dataset/EDA_Corpus_100_Question.csv \
       --retriever $retriever
    echo "==> Done"
done
echo "==================================="
