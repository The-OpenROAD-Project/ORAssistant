#!/bin/bash -eu

retrievers=(
    "agent-retriever"
)

echo "==================================="
echo "==> Dataset: EDA Corpus"
for retriever in "${retrievers[@]}" ; do
    echo "==> Running tests for $retriever"
    python eval_main.py \
       --base_url http://localhost:8000 \
       --dataset ./dataset/EDA_Corpus_100_Question.csv \
       --retriever $retriever
done
echo "==================================="
