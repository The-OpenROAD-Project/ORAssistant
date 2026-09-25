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
# DeepEval 4 scores hallucination as the share of contexts that the answer
# does not contradict (1.0 is clean) and passes a case when score >= threshold.
# A threshold of 0.7 therefore needs at least 70% of contexts not contradicted.
# DeepEval 3 scored the contradicted share with the threshold as a maximum, so
# its 0.7 matches 0.3 here. Pass rates from before the DeepEval 4 bump on
# 2026-09-23 are not comparable with later ones. Sources:
# https://github.com/confident-ai/deepeval/blob/dba2b2908fcf8b7d7cd81871a280374f6dd551e7/deepeval/metrics/hallucination/hallucination.py#L249-L260
# https://github.com/confident-ai/deepeval/blob/dba2b2908fcf8b7d7cd81871a280374f6dd551e7/deepeval/metrics/base_metric.py#L93-L103
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


def make_hallucination_metric(model: DeepEvalBaseLLM) -> HallucinationMetric:
    return HallucinationMetric(
        threshold=HALLUCINATION_THRESHOLD,
        model=model,
        include_reason=True,
    )


if __name__ == "__main__":
    pass
