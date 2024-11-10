from deepeval.metrics import (
    ContextualPrecisionMetric,
    ContextualRecallMetric,
    ContextualRelevancyMetric,
    FaithfulnessMetric,
    HallucinationMetric,
)
from deepeval.models.base_model import DeepEvalBaseLLM

PRECISION_THRESHOLD = 0.7
RECALL_THRESHOLD = 0.7
RELEVANCY_THRESHOLD = 0.7
FAITHFULNESS_THRESHOLD = 0.7
HALLUCINATION_THRESHOLD = 0.7


def make_contextual_precision_metric(
    model: DeepEvalBaseLLM,
) -> ContextualPrecisionMetric:
    return ContextualPrecisionMetric(
        threshold=PRECISION_THRESHOLD,
        model=model,
        include_reason=True,
    )


def make_contextual_recall_metric(model: DeepEvalBaseLLM) -> ContextualRecallMetric:
    return ContextualRecallMetric(
        threshold=RECALL_THRESHOLD,
        model=model,
        include_reason=True,
    )


def make_contextual_relevancy_metric(
    model: DeepEvalBaseLLM,
) -> ContextualRelevancyMetric:
    raise NotImplementedError(
        "ContextualRelevancyMetric is not implemented due to protobuf incompatability"
    )


def make_faithfulness_metric(model: DeepEvalBaseLLM) -> FaithfulnessMetric:
    raise NotImplementedError(
        "FaithfulnessMetric is not implemented due to protobuf incompatability"
    )


def make_hallucination_metric(model: DeepEvalBaseLLM) -> FaithfulnessMetric:
    return HallucinationMetric(
        threshold=HALLUCINATION_THRESHOLD,
        model=model,
        include_reason=True,
    )


if __name__ == "__main__":
    pass
