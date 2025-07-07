import pytest
from unittest.mock import Mock, patch

from src.chains.similarity_retriever_chain import SimilarityRetrieverChain


class TestSimilarityRetrieverChain:
    """Test suite for SimilarityRetrieverChain class."""

    def test_init_with_all_parameters(self):
        """Test SimilarityRetrieverChain initialization with all parameters."""
        mock_llm = Mock()
        mock_vector_db = Mock()
        prompt_template = "Test prompt: {query}"
        embeddings_config = {"type": "HF", "name": "test-model"}
        markdown_docs_path = ["./data/markdown"]
        manpages_path = ["./data/manpages"]
        html_docs_path = ["./data/html"]
        other_docs_path = ["./data/pdf"]

        chain = SimilarityRetrieverChain(
            llm_model=mock_llm,
            prompt_template_str=prompt_template,
            vector_db=mock_vector_db,
            embeddings_config=embeddings_config,
            use_cuda=True,
            chunk_size=1000,
            markdown_docs_path=markdown_docs_path,
            manpages_path=manpages_path,
            html_docs_path=html_docs_path,
            other_docs_path=other_docs_path,
        )

        # Test inherited properties
        assert chain.llm_model == mock_llm
        assert chain.vector_db == mock_vector_db

        # Test SimilarityRetrieverChain specific properties
        assert chain.embeddings_config == embeddings_config
        assert chain.use_cuda is True
        assert chain.chunk_size == 1000
        assert chain.markdown_docs_path == markdown_docs_path
        assert chain.manpages_path == manpages_path
        assert chain.html_docs_path == html_docs_path
        assert chain.other_docs_path == other_docs_path

    def test_init_with_minimal_parameters(self):
        """Test SimilarityRetrieverChain initialization with minimal parameters."""
        chain = SimilarityRetrieverChain()

        # Test defaults
        assert chain.llm_model is None
        assert chain.vector_db is None
        assert chain.embeddings_config is None
        assert chain.use_cuda is False
        assert chain.chunk_size == 500  # default
        assert chain.markdown_docs_path is None
        assert chain.manpages_path is None
        assert chain.html_docs_path is None
        assert chain.other_docs_path is None

    def test_instance_counter_and_naming(self):
        """Test that instance counter works and names are generated correctly."""
        # Get current count
        initial_count = SimilarityRetrieverChain.count

        chain1 = SimilarityRetrieverChain()
        chain2 = SimilarityRetrieverChain()
        chain3 = SimilarityRetrieverChain()

        # Test that count incremented
        assert SimilarityRetrieverChain.count == initial_count + 3

        # Test that names are generated correctly
        assert chain1.name == f"similarity_INST{initial_count + 1}"
        assert chain2.name == f"similarity_INST{initial_count + 2}"
        assert chain3.name == f"similarity_INST{initial_count + 3}"

    def test_inherits_from_base_chain(self):
        """Test that SimilarityRetrieverChain properly inherits from BaseChain."""
        mock_llm = Mock()
        prompt_template = "Test prompt: {query}"

        chain = SimilarityRetrieverChain(
            llm_model=mock_llm, prompt_template_str=prompt_template
        )

        # Test that it has BaseChain methods
        assert hasattr(chain, "create_llm_chain")
        assert hasattr(chain, "get_llm_chain")
        assert hasattr(chain, "prompt_template")

        # Test that BaseChain initialization worked
        assert chain.llm_model == mock_llm
        assert chain.llm_chain is None  # Not created yet

    def test_embeddings_config_parameter(self):
        """Test embeddings configuration parameter handling."""
        hf_config = {"type": "HF", "name": "sentence-transformers/all-MiniLM-L6-v2"}
        google_config = {"type": "GOOGLE_GENAI", "name": "models/embedding-001"}

        chain1 = SimilarityRetrieverChain(embeddings_config=hf_config)
        chain2 = SimilarityRetrieverChain(embeddings_config=google_config)

        assert chain1.embeddings_config == hf_config
        assert chain2.embeddings_config == google_config

    def test_cuda_parameter(self):
        """Test CUDA parameter handling."""
        chain_cpu = SimilarityRetrieverChain(use_cuda=False)
        chain_gpu = SimilarityRetrieverChain(use_cuda=True)

        assert chain_cpu.use_cuda is False
        assert chain_gpu.use_cuda is True

    def test_chunk_size_parameter(self):
        """Test chunk size parameter handling."""
        chain_small = SimilarityRetrieverChain(chunk_size=100)
        chain_large = SimilarityRetrieverChain(chunk_size=2000)

        assert chain_small.chunk_size == 100
        assert chain_large.chunk_size == 2000

    def test_document_paths_parameters(self):
        """Test document paths parameters."""
        markdown_paths = ["./data/markdown", "./docs/md"]
        manpage_paths = ["./data/manpages"]
        html_paths = ["./data/html", "./docs/html"]
        other_paths = ["./data/pdf", "./docs/pdf"]

        chain = SimilarityRetrieverChain(
            markdown_docs_path=markdown_paths,
            manpages_path=manpage_paths,
            html_docs_path=html_paths,
            other_docs_path=other_paths,
        )

        assert chain.markdown_docs_path == markdown_paths
        assert chain.manpages_path == manpage_paths
        assert chain.html_docs_path == html_paths
        assert chain.other_docs_path == other_paths

    @pytest.mark.unit
    def test_class_variable_independence(self):
        """Test that class variable (count) is shared but instance variables are independent."""
        initial_count = SimilarityRetrieverChain.count

        chain1 = SimilarityRetrieverChain(chunk_size=100)
        chain2 = SimilarityRetrieverChain(chunk_size=200)

        # Class variable should be shared and incremented
        assert chain1.count == chain2.count == initial_count + 2

        # Instance variables should be independent
        assert chain1.chunk_size == 100
        assert chain2.chunk_size == 200
        assert chain1.name != chain2.name

    @pytest.mark.unit
    def test_none_parameters_handling(self):
        """Test that None parameters are handled correctly."""
        chain = SimilarityRetrieverChain(
            llm_model=None,
            prompt_template_str=None,
            vector_db=None,
            embeddings_config=None,
            markdown_docs_path=None,
            manpages_path=None,
            html_docs_path=None,
            other_docs_path=None,
        )

        assert chain.llm_model is None
        assert chain.vector_db is None
        assert chain.embeddings_config is None
        assert chain.markdown_docs_path is None
        assert chain.manpages_path is None
        assert chain.html_docs_path is None
        assert chain.other_docs_path is None

    @pytest.mark.integration
    def test_similarity_retriever_chain_with_mock_components(self):
        """Test SimilarityRetrieverChain with mocked components for integration."""
        # Create mock components
        mock_llm = Mock()
        mock_vector_db = Mock()

        # Create chain with realistic configuration
        chain = SimilarityRetrieverChain(
            llm_model=mock_llm,
            prompt_template_str="Answer the question: {query}",
            vector_db=mock_vector_db,
            embeddings_config={"type": "HF", "name": "all-MiniLM-L6-v2"},
            use_cuda=False,
            chunk_size=500,
            markdown_docs_path=["./data/markdown/OR_docs", "./data/markdown/ORFS_docs"],
            manpages_path=["./data/markdown/manpages"],
            html_docs_path=["./data/html/or_website", "./data/html/yosys_docs"],
            other_docs_path=["./data/pdf/OR_publications"],
        )

        # Test that all components are properly set
        assert chain.llm_model is mock_llm
        assert chain.vector_db is mock_vector_db
        assert chain.embeddings_config["type"] == "HF"
        assert len(chain.markdown_docs_path) == 2
        assert len(chain.html_docs_path) == 2

        # Test that BaseChain methods are available
        assert hasattr(chain, "get_llm_chain")
        assert hasattr(chain, "create_llm_chain")

    def test_multiple_instances_have_unique_names(self):
        """Test that multiple instances get unique names."""
        chains = [SimilarityRetrieverChain() for _ in range(5)]
        names = [chain.name for chain in chains]

        # All names should be unique
        assert len(names) == len(set(names))

        # All names should follow the pattern
        for name in names:
            assert name.startswith("similarity_INST")
            assert name.split("similarity_INST")[1].isdigit()

    @patch("src.chains.similarity_retriever_chain.FAISSVectorDatabase")
    def test_create_vector_db_success(self, mock_faiss_db):
        """Test successful vector database creation."""
        mock_db_instance = Mock()
        mock_faiss_db.return_value = mock_db_instance

        embeddings_config = {"type": "HF", "name": "test-model"}
        chain = SimilarityRetrieverChain(
            embeddings_config=embeddings_config, use_cuda=True
        )

        chain.create_vector_db()

        assert chain.vector_db == mock_db_instance
        mock_faiss_db.assert_called_once_with(
            embeddings_model_name="test-model", embeddings_type="HF", use_cuda=True
        )

    def test_create_vector_db_missing_config_raises_error(self):
        """Test that missing embeddings config raises error."""
        chain = SimilarityRetrieverChain(embeddings_config=None)

        with pytest.raises(
            ValueError, match="Embeddings model config not provided correctly"
        ):
            chain.create_vector_db()

    def test_create_vector_db_incomplete_config_raises_error(self):
        """Test that incomplete embeddings config raises error."""
        # Missing 'name' key
        chain = SimilarityRetrieverChain(embeddings_config={"type": "HF", "name": None})

        with pytest.raises(
            ValueError, match="Embeddings model config not provided correctly"
        ):
            chain.create_vector_db()

        # Missing 'type' key
        chain = SimilarityRetrieverChain(
            embeddings_config={"name": "test-model", "type": None}
        )

        with pytest.raises(
            ValueError, match="Embeddings model config not provided correctly"
        ):
            chain.create_vector_db()

    @patch("src.chains.similarity_retriever_chain.FAISSVectorDatabase")
    def test_embed_docs_creates_vector_db_when_none(self, mock_faiss_db):
        """Test that embed_docs creates vector_db when it's None."""
        mock_db_instance = Mock()
        mock_db_instance.add_md_docs.return_value = [Mock()]
        mock_db_instance.add_md_manpages.return_value = [Mock()]
        mock_db_instance.add_documents.return_value = [Mock()]
        mock_db_instance.add_html.return_value = [Mock()]
        mock_faiss_db.return_value = mock_db_instance

        embeddings_config = {"type": "HF", "name": "test-model"}
        chain = SimilarityRetrieverChain(
            embeddings_config=embeddings_config,
            markdown_docs_path=["./docs"],
            manpages_path=["./manpages"],
            html_docs_path=["./html"],
        )

        # Ensure vector_db is None initially
        assert chain.vector_db is None

        chain.embed_docs()

        # Should have created vector_db
        assert chain.vector_db == mock_db_instance
        mock_faiss_db.assert_called_once()

    @patch("os.walk")
    def test_embed_docs_processes_pdf_files(self, mock_walk):
        """Test that embed_docs processes PDF files from other_docs_path."""
        # Mock os.walk to return some PDF files
        mock_walk.return_value = [
            ("/path/to/pdfs", [], ["doc1.pdf", "doc2.txt", "doc3.pdf"]),
            ("/path/to/pdfs/subdir", [], ["doc4.pdf"]),
        ]

        mock_vector_db = Mock()
        mock_vector_db.add_documents.return_value = [Mock(), Mock(), Mock()]

        chain = SimilarityRetrieverChain(other_docs_path=["/path/to/pdfs"])
        chain.vector_db = mock_vector_db

        chain.embed_docs()

        # Should have called add_documents with PDF files only
        mock_vector_db.add_documents.assert_called_once()
        call_args = mock_vector_db.add_documents.call_args
        pdf_files = call_args[1]["folder_paths"]

        # Should contain only PDF files
        assert len(pdf_files) == 3
        assert all(f.endswith(".pdf") for f in pdf_files)
        assert "/path/to/pdfs/doc1.pdf" in pdf_files
        assert "/path/to/pdfs/doc3.pdf" in pdf_files
        assert "/path/to/pdfs/subdir/doc4.pdf" in pdf_files

    def test_embed_docs_saves_database(self):
        """Test that embed_docs saves the database."""
        mock_vector_db = Mock()

        chain = SimilarityRetrieverChain()
        chain.vector_db = mock_vector_db

        chain.embed_docs()

        # Should save database with chain name
        mock_vector_db.save_db.assert_called_once_with(chain.name)

    def test_embed_docs_skips_none_paths(self):
        """Test that embed_docs skips processing when paths are None."""
        mock_vector_db = Mock()

        chain = SimilarityRetrieverChain(
            markdown_docs_path=None,
            manpages_path=None,
            other_docs_path=None,
            html_docs_path=None,
        )
        chain.vector_db = mock_vector_db

        chain.embed_docs()

        # Should not call any add methods
        mock_vector_db.add_md_docs.assert_not_called()
        mock_vector_db.add_md_manpages.assert_not_called()
        mock_vector_db.add_documents.assert_not_called()
        mock_vector_db.add_html.assert_not_called()

        # Should still save database
        mock_vector_db.save_db.assert_called_once()

    def test_create_similarity_retriever_success(self):
        """Test successful similarity retriever creation."""
        mock_vector_db = Mock()
        mock_faiss_db = Mock()
        mock_retriever = Mock()

        mock_vector_db.faiss_db = mock_faiss_db
        mock_faiss_db.as_retriever.return_value = mock_retriever

        chain = SimilarityRetrieverChain()
        chain.vector_db = mock_vector_db

        chain.create_similarity_retriever(search_k=10)

        assert chain.retriever == mock_retriever
        mock_faiss_db.as_retriever.assert_called_once_with(
            search_type="similarity", search_kwargs={"k": 10}
        )

    def test_create_similarity_retriever_when_vector_db_none(self):
        """Test similarity retriever creation when vector_db is None."""
        chain = SimilarityRetrieverChain(
            embeddings_config={"type": "HF", "name": "test-model"}
        )
        chain.vector_db = None

        # Mock the embed_docs method to prevent it from trying to create vector_db
        with patch.object(chain, "embed_docs"):
            with pytest.raises(ValueError, match="FAISS Vector DB not created"):
                chain.create_similarity_retriever()
