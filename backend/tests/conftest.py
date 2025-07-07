import pytest
import sys
from pathlib import Path
from unittest.mock import Mock, patch
import tempfile
import os


@pytest.fixture(scope="session")
def test_data_dir():
    """Get test data directory path."""
    return Path(__file__).parent / "data"


@pytest.fixture
def mock_openai_client():
    """Mock OpenAI client for testing."""
    with patch("openai.OpenAI") as mock_client:
        mock_instance = Mock()
        mock_client.return_value = mock_instance
        yield mock_instance


@pytest.fixture
def mock_langchain_llm():
    """Mock LangChain LLM for testing."""
    with patch("langchain_openai.ChatOpenAI") as mock_llm:
        mock_instance = Mock()
        mock_llm.return_value = mock_instance
        yield mock_instance


@pytest.fixture
def mock_faiss_vectorstore():
    """Mock FAISS vectorstore for testing."""
    with patch("langchain_community.vectorstores.FAISS") as mock_faiss:
        mock_instance = Mock()
        mock_faiss.return_value = mock_instance
        yield mock_instance


@pytest.fixture
def temp_dir():
    """Create a temporary directory for tests."""
    with tempfile.TemporaryDirectory() as temp_dir:
        yield Path(temp_dir)


@pytest.fixture
def sample_documents():
    """Sample documents for testing."""
    return [
        {
            "content": "This is a sample document about OpenROAD installation.",
            "metadata": {"source": "installation.md", "category": "installation"},
        },
        {
            "content": "This document explains OpenROAD flow configuration.",
            "metadata": {"source": "flow.md", "category": "configuration"},
        },
    ]


@pytest.fixture
def mock_env_vars():
    """Mock environment variables for testing."""
    env_vars = {
        "OPENAI_API_KEY": "test-key",
        "GOOGLE_API_KEY": "test-google-key",
        "HUGGINGFACE_API_KEY": "test-hf-key",
    }

    with patch.dict(os.environ, env_vars):
        yield env_vars


@pytest.fixture(autouse=True)
def setup_test_environment():
    """Set up test environment before each test."""
    # Add src directory to Python path
    src_path = Path(__file__).parent.parent / "src"
    if str(src_path) not in sys.path:
        sys.path.insert(0, str(src_path))

    yield

    # Cleanup after test
    if str(src_path) in sys.path:
        sys.path.remove(str(src_path))
