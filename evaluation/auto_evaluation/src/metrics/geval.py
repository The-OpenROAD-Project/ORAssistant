"""
GEval metrics wrapper for DeepEval.
GEval refers to custom LLM-based metrics with non-traditional definitions (e.g. precision, recall, relevancy, etc.)
"""

from deepeval.metrics import GEval
from deepeval.test_case import LLMTestCaseParams
from deepeval.models.base_model import DeepEvalBaseLLM


def make_correctness_metric(model: DeepEvalBaseLLM) -> GEval:
    return GEval(
        name="Correctness",
        criteria="Determine whether the actual output is factually correct based on the expected output.",
        evaluation_steps=[
            "Check whether the facts in 'actual output' contradicts any facts in 'expected output'",
            "You should also heavily penalize omission of detail",
            "Vague language, or contradicting OPINIONS, are OK",
        ],
        evaluation_params=[LLMTestCaseParams.INPUT, LLMTestCaseParams.ACTUAL_OUTPUT],
        model=model,
    )


if __name__ == "__main__":
    pass
