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
            other_docs_path=other_docs_path
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
            llm_model=mock_llm,
            prompt_template_str=prompt_template
        )
        
        # Test that it has BaseChain methods
        assert hasattr(chain, 'create_llm_chain')
        assert hasattr(chain, 'get_llm_chain')
        assert hasattr(chain, 'prompt_template')
        
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
            other_docs_path=other_paths
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
            other_docs_path=None
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
            other_docs_path=["./data/pdf/OR_publications"]
        )
        
        # Test that all components are properly set
        assert chain.llm_model is mock_llm
        assert chain.vector_db is mock_vector_db
        assert chain.embeddings_config["type"] == "HF"
        assert len(chain.markdown_docs_path) == 2
        assert len(chain.html_docs_path) == 2
        
        # Test that BaseChain methods are available
        assert hasattr(chain, 'get_llm_chain')
        assert hasattr(chain, 'create_llm_chain')

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