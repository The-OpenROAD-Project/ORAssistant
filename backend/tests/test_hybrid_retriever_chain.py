import pytest
from unittest.mock import Mock, patch

from src.chains.hybrid_retriever_chain import HybridRetrieverChain


class TestHybridRetrieverChain:
    """Test suite for HybridRetrieverChain class."""

    def test_init_with_all_parameters(self):
        """Test HybridRetrieverChain initialization with all parameters."""
        mock_llm = Mock()
        prompt_template = "Test prompt: {query}"
        embeddings_config = {"type": "HF", "name": "test-model"}
        mock_vector_db = Mock()

        chain = HybridRetrieverChain(
            llm_model=mock_llm,
            prompt_template_str=prompt_template,
            vector_db=mock_vector_db,
            embeddings_config=embeddings_config,
            use_cuda=True,
            chunk_size=1000,
            search_k=10,
            weights=[0.4, 0.3, 0.3],
            markdown_docs_path=["./data/markdown"],
            manpages_path=["./data/manpages"],
            html_docs_path=["./data/html"],
            other_docs_path=["./data/pdf"],
            reranking_model_name="cross-encoder/ms-marco-MiniLM-L-6-v2",
            contextual_rerank=True,
        )

        # Test inherited properties from BaseChain
        assert chain.llm_model == mock_llm
        assert chain.vector_db == mock_vector_db

        # Test HybridRetrieverChain specific properties
        assert chain.embeddings_config == embeddings_config
        assert chain.use_cuda is True
        assert chain.chunk_size == 1000
        assert chain.search_k == 10
        assert chain.weights == [0.4, 0.3, 0.3]
        assert chain.markdown_docs_path == ["./data/markdown"]
        assert chain.manpages_path == ["./data/manpages"]
        assert chain.html_docs_path == ["./data/html"]
        assert chain.other_docs_path == ["./data/pdf"]
        assert chain.reranking_model_name == "cross-encoder/ms-marco-MiniLM-L-6-v2"
        assert chain.contextual_rerank is True

    def test_init_with_minimal_parameters(self):
        """Test HybridRetrieverChain initialization with minimal parameters."""
        chain = HybridRetrieverChain()

        # Test defaults
        assert chain.llm_model is None
        assert chain.vector_db is None
        assert chain.embeddings_config is None
        assert chain.use_cuda is False
        assert chain.chunk_size == 500
        assert chain.search_k == 5
        assert chain.weights == [0.33, 0.33, 0.33]
        assert chain.markdown_docs_path is None
        assert chain.manpages_path is None
        assert chain.html_docs_path is None
        assert chain.other_docs_path is None
        assert chain.reranking_model_name is None
        assert chain.contextual_rerank is False

    def test_inherits_from_base_chain(self):
        """Test that HybridRetrieverChain properly inherits from BaseChain."""
        chain = HybridRetrieverChain()

        # Should have BaseChain methods
        assert hasattr(chain, "create_llm_chain")
        assert hasattr(chain, "get_llm_chain")

        from src.chains.base_chain import BaseChain

        assert isinstance(chain, BaseChain)

    @patch("src.chains.hybrid_retriever_chain.SimilarityRetrieverChain")
    @patch("src.chains.hybrid_retriever_chain.MMRRetrieverChain")
    @patch("src.chains.hybrid_retriever_chain.BM25RetrieverChain")
    @patch("src.chains.hybrid_retriever_chain.EnsembleRetriever")
    def test_create_hybrid_retriever_with_provided_vector_db(
        self, mock_ensemble, mock_bm25_chain, mock_mmr_chain, mock_sim_chain
    ):
        """Test creating hybrid retriever with provided vector database."""
        # Setup mock vector database
        mock_vector_db = Mock()
        mock_vector_db.processed_docs = [Mock(), Mock()]  # Mock some processed docs

        chain = HybridRetrieverChain(vector_db=mock_vector_db)

        # Setup mock chain instances
        mock_sim_instance = Mock()
        mock_sim_instance.retriever = Mock()
        mock_sim_chain.return_value = mock_sim_instance

        mock_mmr_instance = Mock()
        mock_mmr_instance.retriever = Mock()
        mock_mmr_chain.return_value = mock_mmr_instance

        mock_bm25_instance = Mock()
        mock_bm25_instance.retriever = Mock()
        mock_bm25_chain.return_value = mock_bm25_instance

        mock_ensemble_instance = Mock()
        mock_ensemble.return_value = mock_ensemble_instance

        chain.create_hybrid_retriever()

        # Verify similarity retriever chain was created
        mock_sim_chain.assert_called_once()
        mock_sim_instance.create_similarity_retriever.assert_called_once_with(
            search_k=5
        )

        # Verify MMR retriever chain was created
        mock_mmr_chain.assert_called_once()
        mock_mmr_instance.create_mmr_retriever.assert_called_once_with(
            vector_db=mock_vector_db, search_k=5, lambda_mult=0.7
        )

        # Verify BM25 retriever chain was created
        mock_bm25_chain.assert_called_once()
        mock_bm25_instance.create_bm25_retriever.assert_called_once_with(
            embedded_docs=mock_vector_db.processed_docs, search_k=5
        )

        # Verify ensemble retriever was created
        mock_ensemble.assert_called_once_with(
            retrievers=[
                mock_sim_instance.retriever,
                mock_mmr_instance.retriever,
                mock_bm25_instance.retriever,
            ],
            weights=[0.33, 0.33, 0.33],
        )

        assert chain.retriever == mock_ensemble_instance

    @patch("src.chains.hybrid_retriever_chain.SimilarityRetrieverChain")
    @patch("src.chains.hybrid_retriever_chain.MMRRetrieverChain")
    @patch("src.chains.hybrid_retriever_chain.BM25RetrieverChain")
    @patch("src.chains.hybrid_retriever_chain.EnsembleRetriever")
    @patch("src.chains.hybrid_retriever_chain.ContextualCompressionRetriever")
    @patch("src.chains.hybrid_retriever_chain.CrossEncoderReranker")
    @patch("src.chains.hybrid_retriever_chain.HuggingFaceCrossEncoder")
    def test_create_hybrid_retriever_with_contextual_rerank(
        self,
        mock_cross_encoder,
        mock_reranker,
        mock_compression,
        mock_ensemble,
        mock_bm25_chain,
        mock_mmr_chain,
        mock_sim_chain,
    ):
        """Test creating hybrid retriever with contextual reranking enabled."""
        mock_vector_db = Mock()
        mock_vector_db.processed_docs = [Mock(), Mock()]

        chain = HybridRetrieverChain(
            vector_db=mock_vector_db,
            contextual_rerank=True,
            reranking_model_name="cross-encoder/ms-marco-MiniLM-L-6-v2",
        )

        # Setup mocks
        mock_sim_instance = Mock()
        mock_sim_instance.retriever = Mock()
        mock_sim_chain.return_value = mock_sim_instance

        mock_mmr_instance = Mock()
        mock_mmr_instance.retriever = Mock()
        mock_mmr_chain.return_value = mock_mmr_instance

        mock_bm25_instance = Mock()
        mock_bm25_instance.retriever = Mock()
        mock_bm25_chain.return_value = mock_bm25_instance

        mock_ensemble_instance = Mock()
        mock_ensemble.return_value = mock_ensemble_instance

        mock_cross_encoder_instance = Mock()
        mock_cross_encoder.return_value = mock_cross_encoder_instance

        mock_reranker_instance = Mock()
        mock_reranker.return_value = mock_reranker_instance

        mock_compression_instance = Mock()
        mock_compression.return_value = mock_compression_instance

        chain.create_hybrid_retriever()

        # Verify reranking components were created
        mock_cross_encoder.assert_called_once_with(
            model_name="cross-encoder/ms-marco-MiniLM-L-6-v2"
        )
        mock_reranker.assert_called_once_with(
            model=mock_cross_encoder_instance, top_n=5
        )
        mock_compression.assert_called_once_with(
            base_compressor=mock_reranker_instance,
            base_retriever=mock_ensemble_instance,
        )

        assert chain.retriever == mock_compression_instance

    @patch("src.chains.hybrid_retriever_chain.os.path.isdir")
    @patch("src.chains.hybrid_retriever_chain.os.listdir")
    @patch("src.chains.hybrid_retriever_chain.SimilarityRetrieverChain")
    @patch("src.chains.hybrid_retriever_chain.MMRRetrieverChain")
    @patch("src.chains.hybrid_retriever_chain.BM25RetrieverChain")
    @patch("src.chains.hybrid_retriever_chain.EnsembleRetriever")
    def test_create_hybrid_retriever_loads_existing_db(
        self,
        mock_ensemble,
        mock_bm25_chain,
        mock_mmr_chain,
        mock_sim_chain,
        mock_listdir,
        mock_isdir,
    ):
        """Test creating hybrid retriever loads existing database."""
        chain = HybridRetrieverChain(vector_db=None)  # No vector_db provided

        # Mock that database directory exists and contains our database
        mock_isdir.return_value = True
        mock_listdir.return_value = ["similarity_INST_test_db"]

        # Setup similarity chain mock
        mock_sim_instance = Mock()
        mock_sim_instance.name = "similarity_INST_test_db"
        mock_sim_instance.retriever = Mock()
        mock_sim_instance.vector_db = Mock()
        mock_sim_instance.vector_db.get_documents.return_value = [Mock(), Mock()]
        mock_sim_chain.return_value = mock_sim_instance

        # Setup other chain mocks
        mock_mmr_instance = Mock()
        mock_mmr_instance.retriever = Mock()
        mock_mmr_chain.return_value = mock_mmr_instance

        mock_bm25_instance = Mock()
        mock_bm25_instance.retriever = Mock()
        mock_bm25_chain.return_value = mock_bm25_instance

        mock_ensemble.return_value = Mock()

        chain.create_hybrid_retriever()

        # Verify database loading was attempted
        mock_sim_instance.create_vector_db.assert_called_once()
        mock_sim_instance.vector_db.load_db.assert_called_once_with(
            "similarity_INST_test_db"
        )

        # Verify vector_db was assigned
        assert chain.vector_db == mock_sim_instance.vector_db

    @patch("src.chains.hybrid_retriever_chain.os.path.isdir")
    @patch("src.chains.hybrid_retriever_chain.SimilarityRetrieverChain")
    @patch("src.chains.hybrid_retriever_chain.MMRRetrieverChain")
    @patch("src.chains.hybrid_retriever_chain.BM25RetrieverChain")
    @patch("src.chains.hybrid_retriever_chain.EnsembleRetriever")
    def test_create_hybrid_retriever_embeds_docs_when_no_db(
        self, mock_ensemble, mock_bm25_chain, mock_mmr_chain, mock_sim_chain, mock_isdir
    ):
        """Test creating hybrid retriever embeds docs when no existing database."""
        chain = HybridRetrieverChain(vector_db=None)

        # Mock that database directory doesn't exist
        mock_isdir.return_value = False

        # Setup similarity chain mock
        mock_sim_instance = Mock()
        mock_sim_instance.retriever = Mock()
        mock_sim_instance.vector_db = Mock()
        mock_sim_chain.return_value = mock_sim_instance

        # Setup other chain mocks
        mock_mmr_instance = Mock()
        mock_mmr_instance.retriever = Mock()
        mock_mmr_chain.return_value = mock_mmr_instance

        mock_bm25_instance = Mock()
        mock_bm25_instance.retriever = Mock()
        mock_bm25_chain.return_value = mock_bm25_instance

        mock_ensemble.return_value = Mock()

        chain.create_hybrid_retriever()

        # Verify embedding docs was called
        mock_sim_instance.embed_docs.assert_called_once_with(return_docs=True)

        # Verify vector_db was assigned
        assert chain.vector_db == mock_sim_instance.vector_db

    @patch("src.chains.hybrid_retriever_chain.RunnableParallel")
    @patch("src.chains.hybrid_retriever_chain.RunnablePassthrough")
    def test_create_llm_chain(self, mock_passthrough, mock_parallel):
        """Test creating LLM chain with retriever context."""
        chain = HybridRetrieverChain()
        chain.retriever = Mock()

        # Mock the parent create_llm_chain method
        with patch.object(chain, "create_llm_chain", wraps=chain.create_llm_chain) as _:
            with patch("src.chains.base_chain.BaseChain.create_llm_chain"):
                mock_parallel_instance = Mock()
                mock_parallel.return_value = mock_parallel_instance
                mock_parallel_instance.assign.return_value = Mock()

                chain.create_llm_chain()

                # Verify RunnableParallel was created with correct structure
                mock_parallel.assert_called_once_with(
                    {
                        "context": chain.retriever,
                        "question": mock_passthrough.return_value,
                    }
                )

    def test_weights_parameter_validation(self):
        """Test different weight parameter configurations."""
        # Test custom weights
        chain = HybridRetrieverChain(weights=[0.5, 0.3, 0.2])
        assert chain.weights == [0.5, 0.3, 0.2]

        # Test default weights
        chain = HybridRetrieverChain()
        assert chain.weights == [0.33, 0.33, 0.33]

    def test_search_k_parameter_validation(self):
        """Test different search_k parameter values."""
        # Test custom search_k
        chain = HybridRetrieverChain(search_k=10)
        assert chain.search_k == 10

        # Test default search_k
        chain = HybridRetrieverChain()
        assert chain.search_k == 5

    @pytest.mark.unit
    def test_inheritance_chain(self):
        """Test the complete inheritance chain."""
        chain = HybridRetrieverChain()

        # Should inherit from BaseChain
        from src.chains.base_chain import BaseChain

        assert isinstance(chain, BaseChain)

    @pytest.mark.integration
    def test_hybrid_retriever_chain_realistic_workflow(self):
        """Test HybridRetrieverChain with realistic configuration."""
        # Create chain with realistic parameters
        embeddings_config = {"type": "HF", "name": "all-MiniLM-L6-v2"}
        chain = HybridRetrieverChain(
            embeddings_config=embeddings_config,
            chunk_size=500,
            search_k=5,
            weights=[0.4, 0.3, 0.3],
            markdown_docs_path=["./data/markdown/OR_docs"],
            manpages_path=["./data/markdown/manpages"],
            contextual_rerank=True,
            reranking_model_name="cross-encoder/ms-marco-MiniLM-L-6-v2",
        )

        # Test that configuration is properly set
        assert chain.embeddings_config == embeddings_config
        assert chain.chunk_size == 500
        assert chain.search_k == 5
        assert chain.weights == [0.4, 0.3, 0.3]
        assert chain.contextual_rerank is True
        assert chain.reranking_model_name == "cross-encoder/ms-marco-MiniLM-L-6-v2"

    def test_parameters_passed_to_parent(self):
        """Test that parameters are correctly passed to parent class."""
        mock_llm = Mock()
        prompt_template = "Test prompt"
        mock_vector_db = Mock()

        chain = HybridRetrieverChain(
            llm_model=mock_llm,
            prompt_template_str=prompt_template,
            vector_db=mock_vector_db,
        )

        # Verify parent class received the parameters
        assert chain.llm_model == mock_llm
        assert chain.vector_db == mock_vector_db
