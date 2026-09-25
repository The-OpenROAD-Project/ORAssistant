"""
Evaluation script which takes in arguments to dataset and
the model to evaluate on the dataset.
"""

import argparse
import sys
import time
import requests
import os

from dotenv import load_dotenv
from deepeval.test_case import LLMTestCase
from deepeval.evaluate import evaluate

from auto_evaluation.src.models.gemini import GoogleGeminiLangChain
from auto_evaluation.src.metrics.retrieval import (
    make_contextual_precision_metric,
    make_contextual_recall_metric,
    make_hallucination_metric,
)
from auto_evaluation.dataset import hf_pull, preprocess
from auto_evaluation import eval_cases, run_metadata, run_results
from tqdm import tqdm

eval_root_path = os.path.join(os.path.dirname(__file__), "..")
load_dotenv(dotenv_path=os.path.join(eval_root_path, ".env"))

# List of all available retrievers
ALL_RETRIEVERS = {
    "agent-retriever": "/conversations/agent-retriever",
    "agent-retriever-reranker": "/conversations/agent-retriever",
}
RETRY_INTERVAL = 5
RETRY_TIMEOUT = 600
JUDGE_MODEL = "gemini-3.1-pro-preview"

# A run stops when more than this share of questions get no retrieval context
# or the answer "invalid". That means the backend is broken, and the judge
# would only score it 0%.
MAX_EMPTY_RETRIEVAL_SHARE = 0.10


class EmptyRetrievalError(RuntimeError):
    """Too many backend answers had no retrieval context."""

    def __init__(self, message: str, empty_count: int):
        super().__init__(message)
        self.empty_count = empty_count


def check_retrieval(results: list[tuple[str, dict]]) -> int:
    """
    Return how many (question, response) pairs are empty. Raise
    EmptyRetrievalError if there are too many.
    """
    empty = [
        question
        for question, response in results
        if not response["context_sources"]
        or response["response"].strip().lower() == "invalid"
    ]
    if len(empty) > MAX_EMPTY_RETRIEVAL_SHARE * len(results):
        examples = "; ".join(repr(question) for question in empty[:2])
        raise EmptyRetrievalError(
            f"{len(empty)} of {len(results)} questions had no retrieval context "
            f"or the answer 'invalid' (limit {MAX_EMPTY_RETRIEVAL_SHARE:.0%}). "
            f"Examples: {examples}",
            len(empty),
        )
    return len(empty)


class EvaluationHarness:
    # TODO: Use async for EvaluationHarness.
    # TODO: Also requires LLM Engine to be async
    def __init__(self, base_url: str, dataset: str, reranker_base_url: str = ""):
        self.base_url = base_url
        self.dataset = dataset
        self.reranker_base_url = reranker_base_url
        self.qns = preprocess.read_data(self.dataset)
        self.eval_model = GoogleGeminiLangChain(model_name=JUDGE_MODEL)
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

    def evaluate(
        self,
        retriever: str,
        limit: int | None = None,
        *,
        metadata: dict[str, str],
    ):
        retrieval_tcs = []
        response_times = []
        results = []

        # metrics
        precision, recall, hallucination = (
            make_contextual_precision_metric(self.eval_model),
            make_contextual_recall_metric(self.eval_model),
            make_hallucination_metric(self.eval_model),
        )

        # retrieval test cases
        questions = self.qns[:limit] if limit else self.qns
        # Write each case record at once, so a stopped run keeps them.
        with open(eval_cases.CASES_FILE, "w") as cases_file:
            for index, qa_pair in enumerate(tqdm(questions, desc="Evaluating")):
                question, ground_truth = qa_pair["question"], qa_pair["ground_truth"]
                response, response_time = self.query(retriever, question)
                response_text = response["response"]
                context_list = [r["context"] for r in response["context_sources"]]

                case = eval_cases.record(index, question, response)
                eval_cases.append(cases_file, case)
                # Clear the progress bar first, so the line stays whole.
                with tqdm.external_write_mode():
                    print(eval_cases.format_line(case), flush=True)

                # works for: precision, recall, hallucination
                retrieval_tc = LLMTestCase(
                    name=f"test_case_{index}",
                    input=question,
                    actual_output=response_text,
                    expected_output=ground_truth,
                    context=context_list,
                    retrieval_context=context_list,
                    metadata={"tool": case["tool"], "sources": case["sources"]},
                )
                retrieval_tcs.append(retrieval_tc)
                response_times.append(response_time)
                results.append((question, response))

        # Print the metadata before the retrieval check, so a stopped run names
        # its setup too. Flush so progress bars on stderr cannot split the line.
        print(run_metadata.format_line(metadata), flush=True)

        # Check before the judge runs: scoring empty answers costs judge calls
        # and hides a broken backend behind a 0% score. A stopped run still
        # writes its results file, so a baseline reader can skip it.
        try:
            empty_count = check_retrieval(results)
        except EmptyRetrievalError as error:
            run_results.write(
                run_results.RESULTS_FILE,
                metadata,
                len(results),
                error.empty_count,
                None,
            )
            raise

        evaluate(
            test_cases=retrieval_tcs,
            metrics=[precision, recall, hallucination],
            hyperparameters=dict(metadata),
        )

        # parse deepeval results
        metrics = preprocess.read_deepeval_cache()
        run_results.write(
            run_results.RESULTS_FILE, metadata, len(results), empty_count, metrics
        )

    def query(self, retriever: str, query: str) -> tuple[dict, float]:
        """
        Returns the response json and the time taken to get the response (ms)
        """
        endpoint = ALL_RETRIEVERS[retriever]
        url = (
            f"{self.base_url.rstrip('/')}/{endpoint.lstrip('/')}"
            if retriever != "agent-retriever-reranker"
            else f"{self.reranker_base_url.rstrip('/')}/{endpoint.lstrip('/')}"
        )
        payload = {"query": query, "list_context": True, "list_sources": True}
        time.sleep(5)
        response = requests.post(url, json=payload)
        response.raise_for_status()
        return response.json(), response.elapsed.total_seconds() * 1000


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Evaluation script")
    parser.add_argument(
        "--base_url", type=str, help="Base URL of the model to evaluate"
    )
    parser.add_argument(
        "--reranker_base_url", type=str, help="Base URL of the reranker", default=""
    )
    parser.add_argument("--dataset", type=str, help="Path to dataset to evaluate on")
    parser.add_argument("--retriever", type=str, help="Retriever to evaluate on")
    parser.add_argument(
        "--limit", type=int, help="Limit number of questions to evaluate", default=None
    )
    args = parser.parse_args()

    # Pull the dataset from huggingface hub
    dataset_revision = hf_pull.main()

    # Evaluate the model on the dataset
    harness = EvaluationHarness(args.base_url, args.dataset, args.reranker_base_url)
    metadata = run_metadata.collect(JUDGE_MODEL, dataset_revision)
    try:
        harness.evaluate(args.retriever, limit=args.limit, metadata=metadata)
    except EmptyRetrievalError as error:
        sys.exit(f"Retrieval check failed: {error}")
