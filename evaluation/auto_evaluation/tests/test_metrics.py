"""
Unit tests for evaluation metrics module.
Tests verify metric factory functions return correct types,
use correct thresholds, and handle NotImplementedError cases.
"""
import pytest
from unittest.mock import MagicMock
from deepeval.metrics import (
    ContextualPrecisionMetric,
    ContextualRecallMetric,
    HallucinationMetric,
    AnswerRelevancyMetric,
    BiasMetric,
    ToxicityMetric,
    GEval,
)
from deepeval.models.base_model import DeepEvalBaseLLM

from src.metrics.retrieval import (
    make_contextual_precision_metric,
    make_contextual_recall_metric,
    make_contextual_relevancy_metric,
    make_faithfulness_metric,
    make_hallucination_metric,
    PRECISION_THRESHOLD,
    RECALL_THRESHOLD,
    HALLUCINATION_THRESHOLD,
)
from src.metrics.content import (
    make_answer_relevancy_metric,
    make_bias_metric,
    make_toxicity_metric,
    ANSRELEVANCY_THRESHOLD,
    BIAS_THRESHOLD,
    TOXICITY_THRESHOLD,
)
from src.metrics.geval import make_correctness_metric


@pytest.fixture
def mock_model():
    """Mock DeepEvalBaseLLM model for testing."""
    return MagicMock(spec=DeepEvalBaseLLM)


class TestRetrievalMetrics:
    """Tests for retrieval-based evaluation metrics."""

    def test_make_contextual_precision_metric_returns_correct_type(self, mock_model):
        metric = make_contextual_precision_metric(mock_model)
        assert isinstance(metric, ContextualPrecisionMetric)

    def test_make_contextual_precision_metric_threshold(self, mock_model):
        metric = make_contextual_precision_metric(mock_model)
        assert metric.threshold == PRECISION_THRESHOLD

    def test_make_contextual_precision_metric_includes_reason(self, mock_model):
        metric = make_contextual_precision_metric(mock_model)
        assert metric.include_reason is True

    def test_make_contextual_recall_metric_returns_correct_type(self, mock_model):
        metric = make_contextual_recall_metric(mock_model)
        assert isinstance(metric, ContextualRecallMetric)

    def test_make_contextual_recall_metric_threshold(self, mock_model):
        metric = make_contextual_recall_metric(mock_model)
        assert metric.threshold == RECALL_THRESHOLD

    def test_make_contextual_recall_metric_includes_reason(self, mock_model):
        metric = make_contextual_recall_metric(mock_model)
        assert metric.include_reason is True

    def test_make_hallucination_metric_returns_correct_type(self, mock_model):
        metric = make_hallucination_metric(mock_model)
        assert isinstance(metric, HallucinationMetric)

    def test_make_hallucination_metric_threshold(self, mock_model):
        metric = make_hallucination_metric(mock_model)
        assert metric.threshold == HALLUCINATION_THRESHOLD

    def test_make_hallucination_metric_includes_reason(self, mock_model):
        metric = make_hallucination_metric(mock_model)
        assert metric.include_reason is True

    def test_make_contextual_relevancy_metric_raises_not_implemented(self, mock_model):
        """ContextualRelevancyMetric is disabled due to protobuf incompatibility."""
        with pytest.raises(NotImplementedError, match="protobuf incompatability"):
            make_contextual_relevancy_metric(mock_model)

    def test_make_faithfulness_metric_raises_not_implemented(self, mock_model):
        """FaithfulnessMetric is disabled due to protobuf incompatibility."""
        with pytest.raises(NotImplementedError, match="protobuf incompatability"):
            make_faithfulness_metric(mock_model)


class TestContentMetrics:
    """Tests for content-based evaluation metrics."""

    def test_make_answer_relevancy_metric_returns_correct_type(self, mock_model):
        metric = make_answer_relevancy_metric(mock_model)
        assert isinstance(metric, AnswerRelevancyMetric)

    def test_make_answer_relevancy_metric_threshold(self, mock_model):
        metric = make_answer_relevancy_metric(mock_model)
        assert metric.threshold == ANSRELEVANCY_THRESHOLD

    def test_make_answer_relevancy_metric_includes_reason(self, mock_model):
        metric = make_answer_relevancy_metric(mock_model)
        assert metric.include_reason is True

    def test_make_bias_metric_returns_correct_type(self, mock_model):
        metric = make_bias_metric(mock_model)
        assert isinstance(metric, BiasMetric)

    def test_make_bias_metric_threshold(self, mock_model):
        metric = make_bias_metric(mock_model)
        assert metric.threshold == BIAS_THRESHOLD

    def test_make_bias_metric_includes_reason(self, mock_model):
        metric = make_bias_metric(mock_model)
        assert metric.include_reason is True

    def test_make_toxicity_metric_returns_correct_type(self, mock_model):
        metric = make_toxicity_metric(mock_model)
        assert isinstance(metric, ToxicityMetric)

    def test_make_toxicity_metric_threshold(self, mock_model):
        metric = make_toxicity_metric(mock_model)
        assert metric.threshold == TOXICITY_THRESHOLD

    def test_make_toxicity_metric_includes_reason(self, mock_model):
        metric = make_toxicity_metric(mock_model)
        assert metric.include_reason is True


class TestGEvalMetrics:
    """Tests for GEval custom LLM-based metrics."""

    def test_make_correctness_metric_returns_geval(self, mock_model):
        metric = make_correctness_metric(mock_model)
        assert isinstance(metric, GEval)

    def test_make_correctness_metric_name(self, mock_model):
        metric = make_correctness_metric(mock_model)
        assert metric.name == "Correctness"

    def test_make_correctness_metric_has_evaluation_steps(self, mock_model):
        metric = make_correctness_metric(mock_model)
        assert metric.evaluation_steps is not None
        assert len(metric.evaluation_steps) > 0

    def test_make_correctness_metric_has_criteria(self, mock_model):
        metric = make_correctness_metric(mock_model)
        assert metric.criteria is not None
        assert "factually correct" in metric.criteria


class TestThresholdValues:
    """Tests to verify threshold constants are within valid range."""

    def test_precision_threshold_valid(self):
        assert 0.0 <= PRECISION_THRESHOLD <= 1.0

    def test_recall_threshold_valid(self):
        assert 0.0 <= RECALL_THRESHOLD <= 1.0

    def test_hallucination_threshold_valid(self):
        assert 0.0 <= HALLUCINATION_THRESHOLD <= 1.0

    def test_answer_relevancy_threshold_valid(self):
        assert 0.0 <= ANSRELEVANCY_THRESHOLD <= 1.0

    def test_bias_threshold_valid(self):
        assert 0.0 <= BIAS_THRESHOLD <= 1.0

    def test_toxicity_threshold_valid(self):
        assert 0.0 <= TOXICITY_THRESHOLD <= 1.0
