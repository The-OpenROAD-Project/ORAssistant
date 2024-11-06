import os

from dotenv import load_dotenv
from src.models.vertex_ai import GoogleVertexAILangChain

# from src.metrics.geval import make_correctness_metric
from src.metrics.content import (
    make_bias_metric,
    make_toxicity_metric,
    make_answer_relevancy_metric,
)
from src.metrics.retrieval import (
    make_contextual_precision_metric,
    make_contextual_recall_metric,
    make_contextual_relevancy_metric,
    make_faithfulness_metric,
    make_hallucination_metric,
)
from deepeval.test_case import LLMTestCase
from deepeval import evaluate

cur_dir = os.path.dirname(__file__)
root_dir = os.path.join(cur_dir, "../../")
load_dotenv(os.path.join(root_dir, ".env"))

if __name__ == "__main__":
    model = GoogleVertexAILangChain(model_name="gemini-1.5-pro-002")
    print("Retrieval metrics")
    precision, recall, relevancy, faithfulness, hallucination = (
        make_contextual_precision_metric(model),
        make_contextual_recall_metric(model),
        make_contextual_relevancy_metric(model),
        make_faithfulness_metric(model),
        make_hallucination_metric(model),
    )

    test_case = LLMTestCase(
        input="What if these shoes don't fit?",
        actual_output="We offer a 30-day full refund at no extra cost.",
        expected_output="You are eligible for a 30 day full refund at no extra cost.",
        context=[
            "All customers are eligible for a 30 day full refund at no extra cost."
        ],
        retrieval_context=[
            "All customers are eligible for a 30 day full refund at no extra cost."
        ],
    )
    evaluate([test_case], [precision, recall, relevancy, faithfulness, hallucination])
    os.rename(".deepeval-cache.json", "retrieval_metrics.json")

    print("Content metrics")
    answer_relevancy, bias, toxicity = (
        make_answer_relevancy_metric(model),
        make_bias_metric(model),
        make_toxicity_metric(model),
    )

    test_case = LLMTestCase(
        input="What is the capital of France?",
        actual_output="The capital of France is Paris.",
        expected_output="Paris.",
    )
    evaluate([test_case], [answer_relevancy, bias, toxicity])
    os.rename(".deepeval-cache.json", "content_metrics.json")
