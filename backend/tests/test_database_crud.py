"""Unit tests for database CRUD operations."""

import pytest
from uuid import uuid4, UUID
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from src.database.models import Base
from src.database import crud


@pytest.fixture
def db_session():
    """Create an in-memory SQLite database for testing."""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    SessionLocal = sessionmaker(bind=engine)
    session = SessionLocal()
    yield session
    session.close()


class TestConversationCRUD:
    """Test suite for Conversation CRUD operations."""

    def test_create_conversation_with_uuid(self, db_session: Session):
        """Test creating conversation with specific UUID."""
        test_uuid = uuid4()
        conv = crud.create_conversation(
            db_session, conversation_uuid=test_uuid, title="Test Conversation"
        )

        assert conv.uuid == test_uuid
        assert conv.title == "Test Conversation"
        assert conv.created_at is not None
        assert conv.updated_at is not None

    def test_create_conversation_generates_uuid(self, db_session: Session):
        """Test auto-generation of UUID for new conversation."""
        conv = crud.create_conversation(db_session, title="Auto UUID")

        assert conv.uuid is not None
        assert isinstance(conv.uuid, UUID)
        assert conv.title == "Auto UUID"

    def test_create_conversation_without_title(self, db_session: Session):
        """Test creating conversation without title."""
        conv = crud.create_conversation(db_session)

        assert conv.uuid is not None
        assert conv.title is None

    def test_get_conversation_exists(self, db_session: Session):
        """Test retrieving existing conversation."""
        conv = crud.create_conversation(db_session, title="Test")

        retrieved = crud.get_conversation(db_session, conv.uuid)

        assert retrieved is not None
        assert retrieved.uuid == conv.uuid
        assert retrieved.title == "Test"

    def test_get_conversation_not_exists(self, db_session: Session):
        """Test retrieving non-existent conversation returns None."""
        fake_uuid = uuid4()

        result = crud.get_conversation(db_session, fake_uuid)

        assert result is None

    def test_get_or_create_existing_conversation(self, db_session: Session):
        """Test get_or_create returns existing conversation."""
        conv = crud.create_conversation(db_session, title="Original")

        result = crud.get_or_create_conversation(
            db_session, conversation_uuid=conv.uuid, title="Modified"
        )

        assert result.uuid == conv.uuid
        assert result.title == "Original"  # Should not update existing

    def test_get_or_create_new_conversation(self, db_session: Session):
        """Test get_or_create creates new conversation if not exists."""
        test_uuid = uuid4()

        result = crud.get_or_create_conversation(
            db_session, conversation_uuid=test_uuid, title="New"
        )

        assert result.uuid == test_uuid
        assert result.title == "New"

    def test_get_or_create_without_uuid(self, db_session: Session):
        """Test get_or_create without UUID creates new conversation."""
        result = crud.get_or_create_conversation(db_session, title="Auto")

        assert result.uuid is not None
        assert result.title == "Auto"

    def test_get_all_conversations_empty(self, db_session: Session):
        """Test get_all_conversations returns empty list when no conversations."""
        conversations = crud.get_all_conversations(db_session)

        assert conversations == []

    def test_get_all_conversations_ordered(self, db_session: Session):
        """Test get_all_conversations returns conversations ordered by updated_at desc."""
        conv1 = crud.create_conversation(db_session, title="First")
        conv2 = crud.create_conversation(db_session, title="Second")
        conv3 = crud.create_conversation(db_session, title="Third")

        conversations = crud.get_all_conversations(db_session)

        assert len(conversations) == 3
        # Most recently updated should be first
        assert conversations[0].uuid == conv3.uuid
        assert conversations[1].uuid == conv2.uuid
        assert conversations[2].uuid == conv1.uuid

    def test_get_all_conversations_pagination(self, db_session: Session):
        """Test get_all_conversations pagination with skip and limit."""
        for i in range(10):
            crud.create_conversation(db_session, title=f"Conv {i}")

        # Get first 5
        page1 = crud.get_all_conversations(db_session, skip=0, limit=5)
        assert len(page1) == 5

        # Get next 5
        page2 = crud.get_all_conversations(db_session, skip=5, limit=5)
        assert len(page2) == 5

        # Ensure different conversations
        assert page1[0].uuid != page2[0].uuid

    def test_update_conversation_title(self, db_session: Session):
        """Test updating conversation title."""
        conv = crud.create_conversation(db_session, title="Original")

        updated = crud.update_conversation_title(db_session, conv.uuid, "Updated Title")

        assert updated is not None
        assert updated.title == "Updated Title"
        assert updated.uuid == conv.uuid

    def test_update_conversation_title_not_exists(self, db_session: Session):
        """Test updating non-existent conversation returns None."""
        fake_uuid = uuid4()

        result = crud.update_conversation_title(db_session, fake_uuid, "New Title")

        assert result is None

    def test_delete_conversation_exists(self, db_session: Session):
        """Test deleting existing conversation."""
        conv = crud.create_conversation(db_session, title="To Delete")

        result = crud.delete_conversation(db_session, conv.uuid)

        assert result is True
        assert crud.get_conversation(db_session, conv.uuid) is None

    def test_delete_conversation_not_exists(self, db_session: Session):
        """Test deleting non-existent conversation returns False."""
        fake_uuid = uuid4()

        result = crud.delete_conversation(db_session, fake_uuid)

        assert result is False

    def test_delete_conversation_cascades_messages(self, db_session: Session):
        """Test cascade deletion of messages when conversation is deleted."""
        conv = crud.create_conversation(db_session, title="Test")
        msg1 = crud.create_message(db_session, conv.uuid, "user", "Hello")
        msg2 = crud.create_message(db_session, conv.uuid, "assistant", "Hi")

        crud.delete_conversation(db_session, conv.uuid)

        # Verify messages are deleted
        messages = crud.get_conversation_messages(db_session, conv.uuid)
        assert len(messages) == 0
        assert crud.get_message(db_session, msg1.uuid) is None
        assert crud.get_message(db_session, msg2.uuid) is None


class TestMessageCRUD:
    """Test suite for Message CRUD operations."""

    def test_create_message_basic(self, db_session: Session):
        """Test creating basic message."""
        conv = crud.create_conversation(db_session, title="Test")

        msg = crud.create_message(db_session, conv.uuid, "user", "Test message")

        assert msg.uuid is not None
        assert msg.conversation_uuid == conv.uuid
        assert msg.role == "user"
        assert msg.content == "Test message"
        assert msg.context_sources is None
        assert msg.tools is None
        assert msg.created_at is not None

    def test_create_message_with_context_sources(self, db_session: Session):
        """Test creating message with context sources."""
        conv = crud.create_conversation(db_session, title="Test")
        context = {
            "sources": [{"source": "https://example.com", "context": "Example context"}]
        }

        msg = crud.create_message(
            db_session,
            conv.uuid,
            "assistant",
            "Response",
            context_sources=context,
        )

        assert msg.context_sources == context

    def test_create_message_with_tools(self, db_session: Session):
        """Test creating message with tools."""
        conv = crud.create_conversation(db_session, title="Test")
        tools = ["retrieve_general", "retrieve_install"]

        msg = crud.create_message(
            db_session,
            conv.uuid,
            "assistant",
            "Response",
            tools=tools,
        )

        assert msg.tools == tools

    def test_get_message_exists(self, db_session: Session):
        """Test retrieving existing message."""
        conv = crud.create_conversation(db_session, title="Test")
        msg = crud.create_message(db_session, conv.uuid, "user", "Hello")

        retrieved = crud.get_message(db_session, msg.uuid)

        assert retrieved is not None
        assert retrieved.uuid == msg.uuid
        assert retrieved.content == "Hello"

    def test_get_message_not_exists(self, db_session: Session):
        """Test retrieving non-existent message returns None."""
        fake_uuid = uuid4()

        result = crud.get_message(db_session, fake_uuid)

        assert result is None

    def test_get_conversation_messages_ordered(self, db_session: Session):
        """Test get_conversation_messages returns messages ordered by created_at."""
        conv = crud.create_conversation(db_session, title="Test")
        msg1 = crud.create_message(db_session, conv.uuid, "user", "First")
        msg2 = crud.create_message(db_session, conv.uuid, "assistant", "Second")
        msg3 = crud.create_message(db_session, conv.uuid, "user", "Third")

        messages = crud.get_conversation_messages(db_session, conv.uuid)

        assert len(messages) == 3
        assert messages[0].uuid == msg1.uuid
        assert messages[1].uuid == msg2.uuid
        assert messages[2].uuid == msg3.uuid

    def test_get_conversation_messages_pagination(self, db_session: Session):
        """Test get_conversation_messages pagination."""
        conv = crud.create_conversation(db_session, title="Test")
        for i in range(10):
            crud.create_message(db_session, conv.uuid, "user", f"Message {i}")

        # Get first 5
        page1 = crud.get_conversation_messages(db_session, conv.uuid, skip=0, limit=5)
        assert len(page1) == 5

        # Get next 5
        page2 = crud.get_conversation_messages(db_session, conv.uuid, skip=5, limit=5)
        assert len(page2) == 5

    def test_get_conversation_messages_empty(self, db_session: Session):
        """Test get_conversation_messages returns empty list for conversation with no messages."""
        conv = crud.create_conversation(db_session, title="Test")

        messages = crud.get_conversation_messages(db_session, conv.uuid)

        assert messages == []

    def test_delete_message_exists(self, db_session: Session):
        """Test deleting existing message."""
        conv = crud.create_conversation(db_session, title="Test")
        msg = crud.create_message(db_session, conv.uuid, "user", "To delete")

        result = crud.delete_message(db_session, msg.uuid)

        assert result is True
        assert crud.get_message(db_session, msg.uuid) is None

    def test_delete_message_not_exists(self, db_session: Session):
        """Test deleting non-existent message returns False."""
        fake_uuid = uuid4()

        result = crud.delete_message(db_session, fake_uuid)

        assert result is False


class TestConversationHistory:
    """Test suite for conversation history formatting."""

    def test_get_conversation_history_empty(self, db_session: Session):
        """Test get_conversation_history with no messages."""
        conv = crud.create_conversation(db_session, title="Test")

        history = crud.get_conversation_history(db_session, conv.uuid)

        assert history == []

    def test_get_conversation_history_complete_pairs(self, db_session: Session):
        """Test get_conversation_history with complete user-AI pairs."""
        conv = crud.create_conversation(db_session, title="Test")
        crud.create_message(db_session, conv.uuid, "user", "Hello")
        crud.create_message(db_session, conv.uuid, "assistant", "Hi there")
        crud.create_message(db_session, conv.uuid, "user", "How are you?")
        crud.create_message(db_session, conv.uuid, "assistant", "I'm good")

        history = crud.get_conversation_history(db_session, conv.uuid)

        assert len(history) == 2
        assert history[0] == {"User": "Hello", "AI": "Hi there"}
        assert history[1] == {"User": "How are you?", "AI": "I'm good"}

    def test_get_conversation_history_incomplete_pair_trailing_user(
        self, db_session: Session
    ):
        """Test get_conversation_history handles trailing user message without AI response."""
        conv = crud.create_conversation(db_session, title="Test")
        crud.create_message(db_session, conv.uuid, "user", "Hello")
        crud.create_message(db_session, conv.uuid, "assistant", "Hi")
        crud.create_message(db_session, conv.uuid, "user", "Question without answer")

        history = crud.get_conversation_history(db_session, conv.uuid)

        assert len(history) == 2
        assert history[0] == {"User": "Hello", "AI": "Hi"}
        assert history[1] == {"User": "Question without answer"}

    def test_get_conversation_history_multiple_consecutive_users(
        self, db_session: Session
    ):
        """Test get_conversation_history handles multiple consecutive user messages."""
        conv = crud.create_conversation(db_session, title="Test")
        crud.create_message(db_session, conv.uuid, "user", "First")
        crud.create_message(db_session, conv.uuid, "user", "Second")
        crud.create_message(db_session, conv.uuid, "assistant", "Response")

        history = crud.get_conversation_history(db_session, conv.uuid)

        # First user message should be saved as incomplete pair,
        # then second user message pairs with AI response
        assert len(history) == 2
        assert history[0] == {"User": "First"}
        assert history[1] == {"User": "Second", "AI": "Response"}

    def test_get_conversation_history_assistant_without_user(self, db_session: Session):
        """Test get_conversation_history handles assistant message without preceding user message."""
        conv = crud.create_conversation(db_session, title="Test")
        crud.create_message(db_session, conv.uuid, "assistant", "Unpaired AI message")
        crud.create_message(db_session, conv.uuid, "user", "Hello")
        crud.create_message(db_session, conv.uuid, "assistant", "Hi")

        history = crud.get_conversation_history(db_session, conv.uuid)

        # First AI message should be ignored (no current_pair)
        assert len(history) == 1
        assert history[0] == {"User": "Hello", "AI": "Hi"}

    def test_get_conversation_history_only_user_messages(self, db_session: Session):
        """Test get_conversation_history with only user messages."""
        conv = crud.create_conversation(db_session, title="Test")
        crud.create_message(db_session, conv.uuid, "user", "Message 1")
        crud.create_message(db_session, conv.uuid, "user", "Message 2")

        history = crud.get_conversation_history(db_session, conv.uuid)

        # Each user message creates incomplete pair
        assert len(history) == 2
        assert history[0] == {"User": "Message 1"}
        assert history[1] == {"User": "Message 2"}

    def test_get_conversation_history_only_assistant_messages(
        self, db_session: Session
    ):
        """Test get_conversation_history with only assistant messages."""
        conv = crud.create_conversation(db_session, title="Test")
        crud.create_message(db_session, conv.uuid, "assistant", "Message 1")
        crud.create_message(db_session, conv.uuid, "assistant", "Message 2")

        history = crud.get_conversation_history(db_session, conv.uuid)

        # Assistant messages without user messages should be ignored
        assert len(history) == 0
