import pytest
from unittest.mock import Mock, patch
from langchain.docstore.document import Document

from src.chains.bm25_retriever_chain import BM25RetrieverChain


class TestBM25RetrieverChain:
    """Test suite for BM25RetrieverChain class."""

    def test_init_with_all_parameters(self):
        """Test BM25RetrieverChain initialization with all parameters."""
        mock_llm = Mock()
        prompt_template = "Test prompt: {query}"
        embeddings_config = {"type": "HF", "name": "test-model"}

        chain = BM25RetrieverChain(
            llm_model=mock_llm,
            prompt_template_str=prompt_template,
            embeddings_config=embeddings_config,
            use_cuda=True,
            chunk_size=1000,
            markdown_docs_path=["./data/markdown"],
            manpages_path=["./data/manpages"],
            html_docs_path=["./data/html"],
            other_docs_path=["./data/pdf"],
        )

        # Test inherited properties from SimilarityRetrieverChain
        assert chain.llm_model == mock_llm
        assert chain.embeddings_config == embeddings_config
        assert chain.use_cuda is True
        assert chain.chunk_size == 1000

        # Test BM25RetrieverChain specific properties
        assert chain.retriever is None

    def test_init_with_minimal_parameters(self):
        """Test BM25RetrieverChain initialization with minimal parameters."""
        chain = BM25RetrieverChain()

        # Test defaults
        assert chain.llm_model is None
        assert chain.embeddings_config is None
        assert chain.use_cuda is False
        assert chain.chunk_size == 500
        assert chain.retriever is None

    def test_inherits_from_similarity_retriever_chain(self):
        """Test that BM25RetrieverChain properly inherits from SimilarityRetrieverChain."""
        chain = BM25RetrieverChain()

        # Should have SimilarityRetrieverChain methods
        assert hasattr(chain, "name")
        assert hasattr(chain, "embeddings_config")
        assert hasattr(chain, "markdown_docs_path")

        # Should have BaseChain methods via inheritance
        assert hasattr(chain, "create_llm_chain")
        assert hasattr(chain, "get_llm_chain")

    @patch("src.chains.bm25_retriever_chain.BM25Retriever")
    def test_create_bm25_retriever_with_provided_docs(self, mock_bm25_retriever):
        """Test creating BM25 retriever with provided documents."""
        mock_retriever = Mock()
        mock_bm25_retriever.from_documents.return_value = mock_retriever

        chain = BM25RetrieverChain()

        # Provide documents directly
        sample_docs = [
            Document(page_content="Test content 1", metadata={"source": "test1.md"}),
            Document(page_content="Test content 2", metadata={"source": "test2.md"}),
        ]

        chain.create_bm25_retriever(embedded_docs=sample_docs, search_k=3)

        assert chain.retriever is mock_retriever
        mock_bm25_retriever.from_documents.assert_called_once_with(
            documents=sample_docs, search_kwargs={"k": 3}
        )

    @patch("src.chains.bm25_retriever_chain.BM25Retriever")
    def test_create_bm25_retriever_with_default_search_k(self, mock_bm25_retriever):
        """Test creating BM25 retriever with default search_k parameter."""
        mock_retriever = Mock()
        mock_bm25_retriever.from_documents.return_value = mock_retriever

        chain = BM25RetrieverChain()

        sample_docs = [
            Document(page_content="Test content", metadata={"source": "test.md"})
        ]

        chain.create_bm25_retriever(embedded_docs=sample_docs)

        # Should use default search_k=5
        mock_bm25_retriever.from_documents.assert_called_once_with(
            documents=sample_docs, search_kwargs={"k": 5}
        )

    # Note: Skipping complex parent method tests that require extensive mocking
    # These tests would require mocking the entire SimilarityRetrieverChain workflow
    # @patch('src.chains.bm25_retriever_chain.BM25Retriever')
    # def test_create_bm25_retriever_without_provided_docs(self, mock_bm25_retriever):
    #     """Test creating BM25 retriever without provided documents (calls parent methods)."""
    #     pass

    @patch("src.chains.bm25_retriever_chain.BM25Retriever")
    def test_create_bm25_retriever_with_document_list(self, mock_bm25_retriever):
        """Test creating BM25 retriever with a list of documents."""
        mock_retriever = Mock()
        mock_bm25_retriever.from_documents.return_value = mock_retriever

        chain = BM25RetrieverChain()

        # Test with a regular list of documents
        docs = [
            Document(page_content="Doc1", metadata={"source": "doc1.md"}),
            Document(page_content="Doc2", metadata={"source": "doc2.md"}),
        ]

        chain.create_bm25_retriever(embedded_docs=docs)

        # Should pass all documents directly to BM25Retriever
        call_args = mock_bm25_retriever.from_documents.call_args
        documents = call_args[1]["documents"]
        assert len(documents) == 2
        assert documents == docs

    def test_retriever_property_initial_state(self):
        """Test that retriever property starts as None."""
        chain = BM25RetrieverChain()
        assert chain.retriever is None

    @patch("src.chains.bm25_retriever_chain.BM25Retriever")
    def test_retriever_property_after_creation(self, mock_bm25_retriever):
        """Test that retriever property is set after creation."""
        mock_retriever = Mock()
        mock_bm25_retriever.from_documents.return_value = mock_retriever

        chain = BM25RetrieverChain()

        sample_docs = [Document(page_content="Test", metadata={"source": "test.md"})]
        chain.create_bm25_retriever(embedded_docs=sample_docs)

        assert chain.retriever is mock_retriever

    @pytest.mark.unit
    def test_inheritance_chain(self):
        """Test the complete inheritance chain."""
        chain = BM25RetrieverChain()

        # Should inherit from SimilarityRetrieverChain
        from src.chains.similarity_retriever_chain import SimilarityRetrieverChain

        assert isinstance(chain, SimilarityRetrieverChain)

        # Should also inherit from BaseChain (via SimilarityRetrieverChain)
        from src.chains.base_chain import BaseChain

        assert isinstance(chain, BaseChain)

    @pytest.mark.integration
    def test_bm25_retriever_chain_realistic_workflow(self):
        """Test BM25RetrieverChain with realistic configuration."""
        # Create chain with realistic parameters
        chain = BM25RetrieverChain(
            prompt_template_str="Answer the question: {query}",
            embeddings_config={"type": "HF", "name": "all-MiniLM-L6-v2"},
            chunk_size=500,
            markdown_docs_path=["./data/markdown/OR_docs"],
            manpages_path=["./data/markdown/manpages"],
        )

        # Test that configuration is properly set
        assert chain.chunk_size == 500
        assert chain.embeddings_config["type"] == "HF"
        assert len(chain.markdown_docs_path) == 1
        assert len(chain.manpages_path) == 1
        assert chain.retriever is None

        # Test that it has the expected name pattern (from SimilarityRetrieverChain)
        assert hasattr(chain, "name")
        assert chain.name.startswith("similarity_INST")

    def test_parameters_passed_to_parent(self):
        """Test that parameters are correctly passed to parent class."""
        embeddings_config = {"type": "GOOGLE_GENAI", "name": "models/embedding-001"}

        chain = BM25RetrieverChain(
            embeddings_config=embeddings_config,
            use_cuda=True,
            chunk_size=1000,
            markdown_docs_path=["path1", "path2"],
            html_docs_path=["html_path"],
        )

        # Verify parent class received the parameters
        assert chain.embeddings_config == embeddings_config
        assert chain.use_cuda is True
        assert chain.chunk_size == 1000
        assert chain.markdown_docs_path == ["path1", "path2"]
        assert chain.html_docs_path == ["html_path"]
