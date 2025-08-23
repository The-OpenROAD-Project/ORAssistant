"""
Evaluation script which takes in arguments to dataset and
the model to evaluate on the dataset.
"""

import argparse
import time
import requests
import os
import backoff
import asyncio
from typing import List

from dotenv import load_dotenv
from deepeval.test_case import LLMTestCase
from deepeval import evaluate
from deepeval.models import GeminiModel
from deepeval.metrics.base_metric import BaseMetric

from auto_evaluation.src.metrics.retrieval import (
    make_contextual_precision_metric,
    make_contextual_recall_metric,
    make_hallucination_metric,
)
from auto_evaluation.dataset import hf_pull, preprocess
from tqdm import tqdm

eval_root_path = os.path.join(os.path.dirname(__file__), "..")
load_dotenv(dotenv_path=os.path.join(eval_root_path, ".env"))

# List of all available retrievers
ALL_RETRIEVERS = {
    "agent-retriever": "/graphs/agent-retriever",
    "agent-retriever-reranker": "/graphs/agent-retriever",
    "hybrid": "/graphs/hybrid",
    "sim": "/graphs/sim",
    "ensemble": "/graphs/ensemble",
}
RETRY_INTERVAL = 5
RETRY_TIMEOUT = 600
BATCH_SIZE = 5
DELAY_BETWEEN_BATCHES = 10
MAX_RETRIES = 3
BASE_DELAY = 2


class EvaluationHarness:
    # TODO: Use async for EvaluationHarness.
    # TODO: Also requires LLM Engine to be async
    def __init__(
        self,
        base_url: str,
        dataset: str,
        reranker_base_url: str = "",
        batch_size: int = BATCH_SIZE,
        delay_between_batches: int = DELAY_BETWEEN_BATCHES,
        max_retries: int = MAX_RETRIES,
        base_delay: int = BASE_DELAY,
    ):
        self.base_url = base_url
        self.dataset = dataset
        self.reranker_base_url = reranker_base_url
        self.batch_size = batch_size
        self.delay_between_batches = delay_between_batches
        self.max_retries = max_retries
        self.base_delay = base_delay
        self.qns = preprocess.read_data(self.dataset)
        self.eval_model = GeminiModel(
            model_name="gemini-1.5-pro-002",
            project=os.getenv("GOOGLE_PROJECT_ID", ""),
            location=os.getenv("GOOGLE_CLOUD_LOCATION", "us-central1"),
        )
        self.log_dir = "logs"
        os.makedirs(self.log_dir, exist_ok=True)
        self.sanity_check()

    def sanity_check(self):
        cur_time = time.time()
        if not os.path.exists(self.dataset):
            raise ValueError("Dataset path does not exist")
        while time.time() - cur_time < RETRY_TIMEOUT:
            try:
                if not requests.get(f"{self.base_url}/healthcheck").status_code == 200:
                    print("Endpoint not ready, retrying...")
                    time.sleep(RETRY_INTERVAL)
                    continue
                if (
                    self.reranker_base_url
                    and not requests.get(
                        f"{self.reranker_base_url}/healthcheck"
                    ).status_code
                    == 200
                ):
                    print("Reranker endpoint not ready, retrying...")
                    time.sleep(RETRY_INTERVAL)
                    continue
                # All checks passed
                return
            except requests.exceptions.RequestException:
                print("Connection failed, retrying...")
                time.sleep(RETRY_INTERVAL)
                continue
        raise ValueError("Sanity check failed after timeout")

    def evaluate_batch(
        self, test_cases: List[LLMTestCase], metrics: List[BaseMetric]
    ) -> None:
        """Evaluate a batch of test cases with retry logic."""

        @backoff.on_exception(
            backoff.expo,
            Exception,
            giveup=lambda e: "429" not in str(e) and "RESOURCE_EXHAUSTED" not in str(e),
            max_tries=self.max_retries + 1,
            jitter=backoff.random_jitter,
            base=self.base_delay,
        )
        def _evaluate_batch():
            evaluate(
                test_cases=test_cases,
                metrics=metrics,
                print_results=False,
                disable_tqdm=True,
            )

        _evaluate_batch()

    async def evaluate_with_rate_limiting(
        self, test_cases: List[LLMTestCase], metrics: List[BaseMetric]
    ) -> None:
        """Evaluate test cases in batches with rate limiting."""
        total_batches = (len(test_cases) + self.batch_size - 1) // self.batch_size
        print(f"Evaluating {len(test_cases)} test cases in {total_batches} batches")

        async def process_batch(batch_num: int, batch: List[LLMTestCase]) -> None:
            """Process a single batch with rate limiting."""
            print(f"Batch {batch_num}/{total_batches}")
            self.evaluate_batch(batch, metrics)

        # Process batches sequentially with async delays for rate limiting
        for batch_start in range(0, len(test_cases), self.batch_size):
            batch_num = batch_start // self.batch_size + 1
            batch = test_cases[batch_start : batch_start + self.batch_size]

            await process_batch(batch_num, batch)

            # Add delay between batches (except for the last batch)
            if batch_start + self.batch_size < len(test_cases):
                await asyncio.sleep(self.delay_between_batches)

    async def evaluate(self, retriever: str):
        retrieval_tcs = []
        response_times = []

        # metrics
        precision, recall, hallucination = (
            make_contextual_precision_metric(self.eval_model),
            make_contextual_recall_metric(self.eval_model),
            make_hallucination_metric(self.eval_model),
        )

        # retrieval test cases
        for _i, qa_pair in enumerate(tqdm(self.qns, desc="Evaluating")):
            question, ground_truth = qa_pair["question"], qa_pair["ground_truth"]
            response, response_time = self.query(retriever, question)
            response_text = response["response"]
            context_list = [r["context"] for r in response["context_sources"]]

            # works for: precision, recall, hallucination
            retrieval_tc = LLMTestCase(
                input=question,
                actual_output=response_text,
                expected_output=ground_truth,
                context=context_list,
                retrieval_context=context_list,
            )
            retrieval_tcs.append(retrieval_tc)
            response_times.append(response_time)

        # batched evaluate with rate limiting
        await self.evaluate_with_rate_limiting(
            test_cases=retrieval_tcs,
            metrics=[precision, recall, hallucination],
        )

        # parse deepeval results
        preprocess.read_deepeval_cache()

    def query(self, retriever: str, query: str) -> tuple[dict, float]:
        """
        Returns the response json and the time taken to get the response (ms)
        """
        endpoint = ALL_RETRIEVERS[retriever]
        url = (
            f"{self.base_url}/{endpoint}"
            if retriever != "agent-retriever-reranker"
            else f"{self.reranker_base_url}/{endpoint}"
        )
        payload = {"query": query, "list_context": True, "list_sources": False}
        try:
            time.sleep(5)
            response = requests.post(url, json=payload)
            return response.json(), response.elapsed.total_seconds() * 1000
        except Exception as e:
            print(f"Error querying {retriever}: {e}")
            return {
                "response": "invalid",
                "sources": [],
                "context": [],
                "tool": "string",
            }, -999999


async def main():
    parser = argparse.ArgumentParser(description="Evaluation script")
    parser.add_argument(
        "--base_url", type=str, help="Base URL of the model to evaluate"
    )
    parser.add_argument(
        "--reranker_base_url", type=str, help="Base URL of the reranker", default=""
    )
    parser.add_argument("--dataset", type=str, help="Path to dataset to evaluate on")
    parser.add_argument("--retriever", type=str, help="Retriever to evaluate on")
    args = parser.parse_args()

    # Pull the dataset from huggingface hub
    hf_pull.main()

    # Evaluate the model on the dataset
    harness = EvaluationHarness(args.base_url, args.dataset, args.reranker_base_url)
    await harness.evaluate(args.retriever)


if __name__ == "__main__":
    asyncio.run(main())
