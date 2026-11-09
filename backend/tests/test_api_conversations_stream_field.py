"""HTTP tests for the `stream` field of POST /conversations/agent-retriever."""

from unittest.mock import MagicMock, patch
from uuid import uuid4

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from langchain_core.messages import AIMessageChunk

with patch("src.agents.retriever_graph.RetrieverGraph", return_value=MagicMock()):
    from src.api.routers import conversations


async def answer_events(*args, **kwargs):
    """astream_events of one RAG run: the classifier call, then the answer."""
    yield {"event": "on_chat_model_end", "data": {}}
    yield {
        "event": "on_chat_model_stream",
        "data": {"chunk": AIMessageChunk(content="OpenROAD ")},
    }
    yield {
        "event": "on_chat_model_stream",
        "data": {"chunk": AIMessageChunk(content="is a tool.")},
    }


# stream_mode="updates" output of one RAG run.
ANSWER_UPDATES = [
    {"classify": {"agent_type": ["rag_agent"]}},
    {"rag_agent": {"tools": ["retrieve_general"]}},
    {
        "retrieve_general": {
            "context": "ctx",
            "sources": [],
            "urls": ["https://example.com/doc"],
            "context_list": ["ctx"],
        }
    },
    # rag_generate returns the str from the chain's StrOutputParser.
    {"rag_generate": {"messages": ["OpenROAD is a tool."]}},
]


@pytest.fixture
def starting_client():
    """Client for an app whose graph has not finished its startup."""
    conversations.reset_graph_state_for_testing()
    app = FastAPI()
    app.include_router(conversations.router)
    # No database: the endpoint keeps history in memory.
    app.dependency_overrides[conversations.get_optional_db] = lambda: None
    yield TestClient(app)
    conversations.reset_graph_state_for_testing()


@pytest.fixture
def client(starting_client):
    graph = MagicMock()
    graph.graph.astream_events = answer_events
    graph.graph.stream.return_value = iter(ANSWER_UPDATES)
    conversations._rg = graph
    conversations._rg_started.set()
    conversations._rg_ready.set()
    return starting_client


def test_stream_true_returns_an_event_stream(client):
    response = client.post(
        "/conversations/agent-retriever",
        json={"query": "What is OpenROAD?", "stream": True},
    )

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/event-stream")
    assert response.text == "OpenROAD \n\nis a tool.\n\nSources: \n\n"


@pytest.mark.parametrize("stream_field", [{}, {"stream": False}])
def test_stream_absent_or_false_returns_the_json_answer(client, stream_field):
    response = client.post(
        "/conversations/agent-retriever",
        json={
            "query": "What is OpenROAD?",
            "list_sources": True,
            "conversation_uuid": str(uuid4()),
            **stream_field,
        },
    )

    assert response.status_code == 200
    assert response.headers["content-type"] == "application/json"
    assert response.json() == {
        "response": "OpenROAD is a tool.",
        "context_sources": [{"source": "https://example.com/doc", "context": ""}],
        "tools": ["retrieve_general"],
    }


def test_stream_true_before_the_graph_is_ready_reports_the_error_in_band(
    starting_client,
):
    # Same as POST /agent-retriever/stream: the stream has already started,
    # so the error is a stream message, not a 503 as for a JSON answer.
    response = starting_client.post(
        "/conversations/agent-retriever",
        json={"query": "What is OpenROAD?", "stream": True},
    )

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/event-stream")
    assert response.text == (
        "Error: Graph is still initializing. Please retry shortly.\n\n"
    )
