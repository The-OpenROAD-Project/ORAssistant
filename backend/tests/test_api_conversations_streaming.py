"""Unit tests for streaming conversation endpoint."""

import pytest
from unittest.mock import Mock, patch, MagicMock
from uuid import uuid4
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from langchain_core.messages import AIMessageChunk

from src.database.models import Base
from src.database import crud
from src.api.models.response_model import UserInput

# Patch RetrieverGraph globally before any other imports
mock_rg_instance = MagicMock()
mock_graph_global = MagicMock()
mock_rg_instance.graph = mock_graph_global

with patch("src.agents.retriever_graph.RetrieverGraph", return_value=mock_rg_instance):
    # Import after patching
    from src.api.routers import conversations  # noqa: F401


@pytest.fixture
def db_session():
    """Create an in-memory SQLite database for testing."""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    SessionLocal = sessionmaker(bind=engine)
    session = SessionLocal()
    yield session
    session.close()


@pytest.fixture
def mock_retriever_graph():
    """Mock RetrieverGraph for streaming tests."""
    # Reset the mock for each test
    mock_graph_global.reset_mock()
    yield mock_graph_global


@pytest.fixture
def sample_user_input():
    """Sample user input for testing."""
    return UserInput(
        query="What is OpenROAD?",
        list_sources=False,
        list_context=False,
        conversation_uuid=uuid4(),
    )


class TestStreamingEndpoint:
    """Test suite for the streaming endpoint."""

    @pytest.mark.asyncio
    async def test_get_response_stream_basic(
        self, db_session: Session, mock_retriever_graph, sample_user_input: UserInput
    ):
        """Test basic streaming response generation."""
        from src.api.routers.conversations import get_response_stream

        # Mock stream events
        async def mock_astream_events(*args, **kwargs):
            # Simulate retriever events
            yield {
                "event": "on_retriever_end",
                "data": {
                    "output": [
                        Mock(metadata={"url": "https://example.com/doc1"}),
                        Mock(metadata={"url": "https://example.com/doc2"}),
                    ]
                },
            }
            # Simulate first LLM call end
            yield {"event": "on_chat_model_end", "data": {}}
            # Simulate second LLM call streaming
            yield {
                "event": "on_chat_model_stream",
                "data": {"chunk": AIMessageChunk(content="OpenROAD ")},
            }
            yield {
                "event": "on_chat_model_stream",
                "data": {"chunk": AIMessageChunk(content="is a ")},
            }
            yield {
                "event": "on_chat_model_stream",
                "data": {"chunk": AIMessageChunk(content="tool.")},
            }

        mock_retriever_graph.astream_events = mock_astream_events

        # Collect streamed chunks
        chunks = []
        async for chunk in get_response_stream(sample_user_input, db_session):
            chunks.append(chunk)

        # Verify chunks
        assert len(chunks) > 0
        assert any("OpenROAD " in chunk for chunk in chunks)
        assert any("is a " in chunk for chunk in chunks)
        assert any("tool." in chunk for chunk in chunks)
        assert any("Sources:" in chunk for chunk in chunks)
        assert any("example.com/doc1" in chunk for chunk in chunks)

        # Verify conversation and messages were created
        all_conversations = crud.get_all_conversations(db_session)
        assert len(all_conversations) == 1
        conversation = all_conversations[0]
        assert conversation.uuid == sample_user_input.conversation_uuid

        messages = conversation.messages
        assert len(messages) == 2
        assert messages[0].role == "user"
        assert messages[0].content == "What is OpenROAD?"
        assert messages[1].role == "assistant"
        assert "OpenROAD is a tool." in messages[1].content

    @pytest.mark.asyncio
    async def test_get_response_stream_creates_conversation(
        self, db_session: Session, mock_retriever_graph
    ):
        """Test that streaming creates a new conversation if UUID is None."""
        from src.api.routers.conversations import get_response_stream

        user_input = UserInput(
            query="Test question", list_sources=False, conversation_uuid=None
        )

        async def mock_astream_events(*args, **kwargs):
            yield {
                "event": "on_chat_model_stream",
                "data": {"chunk": AIMessageChunk(content="Test response")},
            }
            yield {"event": "on_chat_model_end", "data": {}}
            yield {"event": "on_chat_model_end", "data": {}}

        mock_retriever_graph.astream_events = mock_astream_events

        chunks = []
        async for chunk in get_response_stream(user_input, db_session):
            chunks.append(chunk)

        # Verify conversation was created
        all_conversations = crud.get_all_conversations(db_session)
        assert len(all_conversations) == 1

    @pytest.mark.asyncio
    async def test_get_response_stream_with_chat_history(
        self, db_session: Session, mock_retriever_graph
    ):
        """Test streaming with existing chat history."""
        from src.api.routers.conversations import get_response_stream

        # Create existing conversation with messages
        conv_uuid = uuid4()
        _conv = crud.create_conversation(
            db_session, conversation_uuid=conv_uuid, title="Test"
        )
        crud.create_message(
            db_session,
            conversation_uuid=conv_uuid,
            role="user",
            content="Previous question",
        )
        crud.create_message(
            db_session,
            conversation_uuid=conv_uuid,
            role="assistant",
            content="Previous answer",
        )

        user_input = UserInput(query="Follow-up question", conversation_uuid=conv_uuid)

        captured_inputs = []

        async def mock_astream_events(inputs, *args, **kwargs):
            captured_inputs.append(inputs)
            yield {
                "event": "on_chat_model_stream",
                "data": {"chunk": AIMessageChunk(content="Follow-up answer")},
            }
            yield {"event": "on_chat_model_end", "data": {}}
            yield {"event": "on_chat_model_end", "data": {}}

        mock_retriever_graph.astream_events = mock_astream_events

        chunks = []
        async for chunk in get_response_stream(user_input, db_session):
            chunks.append(chunk)

        # Verify chat history was included in inputs
        assert len(captured_inputs) == 1
        assert "chat_history" in captured_inputs[0]
        chat_history = captured_inputs[0]["chat_history"]
        assert "Previous question" in chat_history
        assert "Previous answer" in chat_history

    @pytest.mark.asyncio
    async def test_get_response_stream_multiple_retrievals(
        self, db_session: Session, mock_retriever_graph, sample_user_input: UserInput
    ):
        """Test streaming with multiple retrieval events."""
        from src.api.routers.conversations import get_response_stream

        async def mock_astream_events(*args, **kwargs):
            # First retrieval
            yield {
                "event": "on_retriever_start",
                "data": {
                    "output": [Mock(metadata={"url": "https://example.com/doc1"})]
                },
            }
            # Second retrieval
            yield {
                "event": "on_retriever_end",
                "data": {
                    "output": [
                        Mock(metadata={"url": "https://example.com/doc2"}),
                        Mock(metadata={"url": "https://example.com/doc3"}),
                    ]
                },
            }
            yield {"event": "on_chat_model_end", "data": {}}
            yield {
                "event": "on_chat_model_stream",
                "data": {"chunk": AIMessageChunk(content="Response")},
            }

        mock_retriever_graph.astream_events = mock_astream_events

        chunks = []
        async for chunk in get_response_stream(sample_user_input, db_session):
            chunks.append(chunk)

        # Verify all unique URLs are in sources
        sources_chunk = [c for c in chunks if "Sources:" in c][0]
        assert "doc1" in sources_chunk
        assert "doc2" in sources_chunk
        assert "doc3" in sources_chunk

    @pytest.mark.asyncio
    async def test_get_response_stream_filters_duplicate_urls(
        self, db_session: Session, mock_retriever_graph, sample_user_input: UserInput
    ):
        """Test that duplicate URLs are filtered out."""
        from src.api.routers.conversations import get_response_stream

        async def mock_astream_events(*args, **kwargs):
            yield {
                "event": "on_retriever_end",
                "data": {
                    "output": [
                        Mock(metadata={"url": "https://example.com/doc1"}),
                        Mock(metadata={"url": "https://example.com/doc1"}),
                        Mock(metadata={"url": "https://example.com/doc2"}),
                    ]
                },
            }
            yield {"event": "on_chat_model_end", "data": {}}
            yield {
                "event": "on_chat_model_stream",
                "data": {"chunk": AIMessageChunk(content="Test")},
            }

        mock_retriever_graph.astream_events = mock_astream_events

        chunks = []
        async for chunk in get_response_stream(sample_user_input, db_session):
            chunks.append(chunk)

        sources_chunk = [c for c in chunks if "Sources:" in c][0]
        # Count occurrences of doc1
        doc1_count = sources_chunk.count("doc1")
        assert doc1_count == 1

    @pytest.mark.asyncio
    async def test_get_response_stream_skips_first_llm_call(
        self, db_session: Session, mock_retriever_graph, sample_user_input: UserInput
    ):
        """Test that streaming only outputs from second LLM call onwards."""
        from src.api.routers.conversations import get_response_stream

        async def mock_astream_events(*args, **kwargs):
            # First LLM call - should be skipped
            yield {
                "event": "on_chat_model_stream",
                "data": {"chunk": AIMessageChunk(content="SHOULD_NOT_APPEAR")},
            }
            yield {"event": "on_chat_model_end", "data": {}}
            # Second LLM call - should be included
            yield {
                "event": "on_chat_model_stream",
                "data": {"chunk": AIMessageChunk(content="SHOULD_APPEAR")},
            }

        mock_retriever_graph.astream_events = mock_astream_events

        chunks = []
        async for chunk in get_response_stream(sample_user_input, db_session):
            chunks.append(chunk)

        content_chunks = [c for c in chunks if "Sources:" not in c]
        assert not any("SHOULD_NOT_APPEAR" in c for c in content_chunks)
        assert any("SHOULD_APPEAR" in c for c in content_chunks)

    @pytest.mark.asyncio
    async def test_get_response_stream_handles_non_ai_message_chunks(
        self, db_session: Session, mock_retriever_graph, sample_user_input: UserInput
    ):
        """Test handling of non-AIMessageChunk content."""
        from src.api.routers.conversations import get_response_stream

        async def mock_astream_events(*args, **kwargs):
            yield {"event": "on_chat_model_end", "data": {}}
            # Send non-AIMessageChunk
            yield {
                "event": "on_chat_model_stream",
                "data": {"chunk": "plain_string"},  # Not an AIMessageChunk
            }
            # Send valid AIMessageChunk
            yield {
                "event": "on_chat_model_stream",
                "data": {"chunk": AIMessageChunk(content="Valid content")},
            }

        mock_retriever_graph.astream_events = mock_astream_events

        chunks = []
        async for chunk in get_response_stream(sample_user_input, db_session):
            chunks.append(chunk)

        # Should only include valid AIMessageChunk
        content_chunks = [c for c in chunks if "Sources:" not in c]
        assert any("Valid content" in c for c in content_chunks)

    @pytest.mark.asyncio
    async def test_get_response_stream_saves_context_sources(
        self, db_session: Session, mock_retriever_graph, sample_user_input: UserInput
    ):
        """Test that context sources are saved to database."""
        from src.api.routers.conversations import get_response_stream

        async def mock_astream_events(*args, **kwargs):
            yield {
                "event": "on_retriever_end",
                "data": {
                    "output": [
                        Mock(metadata={"url": "https://example.com/doc1"}),
                        Mock(metadata={"url": "https://example.com/doc2"}),
                    ]
                },
            }
            yield {"event": "on_chat_model_end", "data": {}}
            yield {
                "event": "on_chat_model_stream",
                "data": {"chunk": AIMessageChunk(content="Response")},
            }

        mock_retriever_graph.astream_events = mock_astream_events

        chunks = []
        async for chunk in get_response_stream(sample_user_input, db_session):
            chunks.append(chunk)

        # Verify context sources in database
        all_conversations = crud.get_all_conversations(db_session)
        conversation = all_conversations[0]
        assistant_message = [m for m in conversation.messages if m.role == "assistant"][
            0
        ]

        assert assistant_message.context_sources is not None
        assert "sources" in assistant_message.context_sources
        sources = assistant_message.context_sources["sources"]
        assert len(sources) == 2
        assert any(s["source"] == "https://example.com/doc1" for s in sources)
        assert any(s["source"] == "https://example.com/doc2" for s in sources)

    @pytest.mark.asyncio
    async def test_get_response_stream_title_truncation(
        self, db_session: Session, mock_retriever_graph
    ):
        """Test that conversation title is truncated to 100 characters."""
        from src.api.routers.conversations import get_response_stream

        long_query = "A" * 150  # 150 characters
        user_input = UserInput(query=long_query, conversation_uuid=None)

        async def mock_astream_events(*args, **kwargs):
            yield {"event": "on_chat_model_end", "data": {}}
            yield {
                "event": "on_chat_model_stream",
                "data": {"chunk": AIMessageChunk(content="Response")},
            }

        mock_retriever_graph.astream_events = mock_astream_events

        chunks = []
        async for chunk in get_response_stream(user_input, db_session):
            chunks.append(chunk)

        all_conversations = crud.get_all_conversations(db_session)
        conversation = all_conversations[0]
        assert len(conversation.title) == 100

    @pytest.mark.asyncio
    async def test_get_agent_response_streaming_endpoint(
        self, db_session: Session, mock_retriever_graph
    ):
        """Test the FastAPI streaming endpoint wrapper."""
        from src.api.routers.conversations import get_agent_response_streaming
        from starlette.responses import StreamingResponse

        user_input = UserInput(query="Test", conversation_uuid=uuid4())

        async def mock_astream_events(*args, **kwargs):
            yield {"event": "on_chat_model_end", "data": {}}
            yield {
                "event": "on_chat_model_stream",
                "data": {"chunk": AIMessageChunk(content="Test response")},
            }

        mock_retriever_graph.astream_events = mock_astream_events

        response = await get_agent_response_streaming(user_input, db_session)

        assert isinstance(response, StreamingResponse)
        assert response.media_type == "text/event-stream"

    @pytest.mark.asyncio
    async def test_get_response_stream_graph_not_initialized(
        self, db_session: Session, sample_user_input: UserInput
    ):
        """Test behavior when graph is not initialized."""
        from src.api.routers.conversations import get_response_stream

        with patch("src.api.routers.conversations.rg") as mock_rg:
            mock_rg.graph = None

            chunks = []
            async for chunk in get_response_stream(sample_user_input, db_session):
                chunks.append(chunk)

            # When graph is None, streaming continues but produces no content chunks
            # Should still have sources line
            assert any("Sources:" in c for c in chunks)

    @pytest.mark.asyncio
    async def test_get_response_stream_empty_content(
        self, db_session: Session, mock_retriever_graph, sample_user_input: UserInput
    ):
        """Test handling of empty message content."""
        from src.api.routers.conversations import get_response_stream

        async def mock_astream_events(*args, **kwargs):
            yield {"event": "on_chat_model_end", "data": {}}
            # Empty content
            yield {
                "event": "on_chat_model_stream",
                "data": {"chunk": AIMessageChunk(content="")},
            }
            # Valid content
            yield {
                "event": "on_chat_model_stream",
                "data": {"chunk": AIMessageChunk(content="Valid")},
            }

        mock_retriever_graph.astream_events = mock_astream_events

        chunks = []
        async for chunk in get_response_stream(sample_user_input, db_session):
            chunks.append(chunk)

        # Should only stream non-empty content
        content_chunks = [c for c in chunks if "Sources:" not in c and c.strip()]
        assert all("Valid" in c for c in content_chunks if c.strip())

    @pytest.mark.asyncio
    async def test_get_response_stream_no_sources(
        self, db_session: Session, mock_retriever_graph, sample_user_input: UserInput
    ):
        """Test streaming when no retrieval sources are found."""
        from src.api.routers.conversations import get_response_stream

        async def mock_astream_events(*args, **kwargs):
            # No retriever events
            yield {"event": "on_chat_model_end", "data": {}}
            yield {
                "event": "on_chat_model_stream",
                "data": {"chunk": AIMessageChunk(content="Response without sources")},
            }

        mock_retriever_graph.astream_events = mock_astream_events

        chunks = []
        async for chunk in get_response_stream(sample_user_input, db_session):
            chunks.append(chunk)

        # Should still have a Sources line (empty)
        assert any("Sources:" in c for c in chunks)
        sources_chunk = [c for c in chunks if "Sources:" in c][0]
        assert sources_chunk.strip() == "Sources:"
