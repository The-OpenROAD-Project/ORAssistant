from deepeval.metrics import (
    FaithfulnessMetric,
    AnswerRelevancyMetric,
    BiasMetric,
    ToxicityMetric,
)
from deepeval.models.base_model import DeepEvalBaseLLM

ANSRELEVANCY_THRESHOLD = 0.7
HALLUCINATION_THRESHOLD = 0.7
BIAS_THRESHOLD = 0.7
TOXICITY_THRESHOLD = 0.7


def make_answer_relevancy_metric(model: DeepEvalBaseLLM) -> FaithfulnessMetric:
    return AnswerRelevancyMetric(
        threshold=ANSRELEVANCY_THRESHOLD,
        model=model,
        include_reason=True,
    )


def make_bias_metric(model: DeepEvalBaseLLM) -> FaithfulnessMetric:
    return BiasMetric(
        threshold=BIAS_THRESHOLD,
        model=model,
        include_reason=True,
    )


def make_toxicity_metric(model: DeepEvalBaseLLM) -> FaithfulnessMetric:
    return ToxicityMetric(
        threshold=TOXICITY_THRESHOLD,
        model=model,
        include_reason=True,
    )
