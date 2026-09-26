"""Tests for the readiness probe while the graph starts in the background."""

import asyncio
from unittest.mock import MagicMock, patch

import pytest

with patch("src.agents.retriever_graph.RetrieverGraph", return_value=MagicMock()):
    from src.api.routers import conversations


@pytest.fixture(autouse=True)
def fresh_graph_state():
    conversations.reset_graph_state_for_testing()
    yield
    conversations.reset_graph_state_for_testing()


def _ready() -> dict[str, str]:
    return asyncio.run(conversations.ready())


def test_ready_reports_initializing_before_the_graph_is_built() -> None:
    assert _ready() == {"status": "initializing"}


def test_ready_reports_ready_after_the_graph_is_built() -> None:
    with patch.object(conversations, "RetrieverGraph"):
        conversations._initialize_graph()

    assert _ready() == {"status": "ready"}


def test_ready_reports_a_failed_start_with_its_error() -> None:
    # For example, a 429 from the embeddings API while the graph builds.
    graph = MagicMock()
    graph.initialize.side_effect = RuntimeError("429 RESOURCE_EXHAUSTED")
    with patch.object(conversations, "RetrieverGraph", return_value=graph):
        with pytest.raises(RuntimeError):
            conversations._initialize_graph()

    assert _ready() == {
        "status": "failed",
        "error": "RuntimeError: 429 RESOURCE_EXHAUSTED",
    }
    assert conversations.get_graph() is None


def test_reset_clears_a_failed_start() -> None:
    graph = MagicMock()
    graph.initialize.side_effect = RuntimeError("boom")
    with patch.object(conversations, "RetrieverGraph", return_value=graph):
        with pytest.raises(RuntimeError):
            conversations._initialize_graph()

    conversations.reset_graph_state_for_testing()

    assert _ready() == {"status": "initializing"}
