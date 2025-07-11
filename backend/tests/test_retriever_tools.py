import pytest
from unittest.mock import Mock, patch

from src.agents.retriever_tools import RetrieverTools


class TestRetrieverTools:
    """Test suite for RetrieverTools class."""

    def test_init(self):
        """Test RetrieverTools initialization."""
        tools = RetrieverTools()

        # Check that it's a valid instance
        assert isinstance(tools, RetrieverTools)

    @patch("src.agents.retriever_tools.HybridRetrieverChain")
    def test_initialize_success(self, mock_hybrid_chain):
        """Test successful initialization of all retrievers."""
        tools = RetrieverTools()

        # Mock the HybridRetrieverChain instances
        mock_chains = []
        for i in range(
            6
        ):  # 6 retrievers: general, install, commands, yosys, klayout, errinfo
            mock_chain = Mock()
            mock_chain.retriever = Mock()
            mock_chains.append(mock_chain)

        mock_hybrid_chain.side_effect = mock_chains

        embeddings_config = {"type": "HF", "name": "test-model"}
        reranking_model_name = "test-reranker"

        tools.initialize(
            embeddings_config=embeddings_config,
            reranking_model_name=reranking_model_name,
            use_cuda=True,
            fast_mode=False,
        )

        # Verify all retrievers are created
        assert mock_hybrid_chain.call_count == 6

        # Verify create_hybrid_retriever is called on all chains
        for mock_chain in mock_chains:
            mock_chain.create_hybrid_retriever.assert_called_once()

        # Verify class attributes are set
        assert RetrieverTools.general_retriever == mock_chains[0].retriever
        assert RetrieverTools.install_retriever == mock_chains[1].retriever
        assert RetrieverTools.commands_retriever == mock_chains[2].retriever
        assert RetrieverTools.yosys_rtdocs_retriever == mock_chains[3].retriever
        assert RetrieverTools.klayout_retriever == mock_chains[4].retriever
        assert RetrieverTools.errinfo_retriever == mock_chains[5].retriever

    @patch("src.agents.retriever_tools.HybridRetrieverChain")
    def test_initialize_with_fast_mode(self, mock_hybrid_chain):
        """Test initialization with fast mode enabled."""
        tools = RetrieverTools()

        # Mock the HybridRetrieverChain instances
        mock_chains = []
        for i in range(6):
            mock_chain = Mock()
            mock_chain.retriever = Mock()
            mock_chains.append(mock_chain)

        mock_hybrid_chain.side_effect = mock_chains

        embeddings_config = {"type": "HF", "name": "test-model"}
        reranking_model_name = "test-reranker"

        tools.initialize(
            embeddings_config=embeddings_config,
            reranking_model_name=reranking_model_name,
            use_cuda=False,
            fast_mode=True,
        )

        # Verify all retrievers are created
        assert mock_hybrid_chain.call_count == 6

        # Check that fast mode configurations are used
        # The general retriever should have different paths for fast mode
        general_call = mock_hybrid_chain.call_args_list[0]
        general_kwargs = general_call[1]

        # In fast mode, html_docs_path should be empty list
        assert general_kwargs["html_docs_path"] == []
        # markdown_docs_path should be the fastmode version
        assert len(general_kwargs["markdown_docs_path"]) == 1
        # other_docs_path should be empty list
        assert general_kwargs["other_docs_path"] == []

    @patch("src.agents.retriever_tools.format_docs")
    def test_retrieve_general_success(self, mock_format_docs):
        """Test successful general retrieval."""
        # Set up mock retriever
        mock_retriever = Mock()
        mock_docs = [Mock(), Mock()]
        mock_retriever.invoke.return_value = mock_docs
        RetrieverTools.general_retriever = mock_retriever

        # Mock format_docs return value
        formatted_result = ("formatted_text", ["source1"], ["url1"], ["context1"])
        mock_format_docs.return_value = formatted_result

        result = RetrieverTools.retrieve_general("test query")

        assert result == formatted_result
        mock_retriever.invoke.assert_called_once_with(input="test query")
        mock_format_docs.assert_called_once_with(mock_docs)

    def test_retrieve_general_not_initialized(self):
        """Test general retrieval when retriever not initialized."""
        RetrieverTools.general_retriever = None

        with pytest.raises(ValueError, match="General Retriever not initialized"):
            RetrieverTools.retrieve_general("test query")

    @patch("src.agents.retriever_tools.format_docs")
    def test_retrieve_cmds_success(self, mock_format_docs):
        """Test successful commands retrieval."""
        # Set up mock retriever
        mock_retriever = Mock()
        mock_docs = [Mock(), Mock()]
        mock_retriever.invoke.return_value = mock_docs
        RetrieverTools.commands_retriever = mock_retriever

        # Mock format_docs return value
        formatted_result = ("formatted_text", ["source1"], ["url1"], ["context1"])
        mock_format_docs.return_value = formatted_result

        result = RetrieverTools.retrieve_cmds("test query")

        assert result == formatted_result
        mock_retriever.invoke.assert_called_once_with(input="test query")
        mock_format_docs.assert_called_once_with(mock_docs)

    def test_retrieve_cmds_not_initialized(self):
        """Test commands retrieval when retriever not initialized."""
        RetrieverTools.commands_retriever = None

        with pytest.raises(ValueError, match="Commands Retriever not initialized"):
            RetrieverTools.retrieve_cmds("test query")

    @patch("src.agents.retriever_tools.format_docs")
    def test_retrieve_install_success(self, mock_format_docs):
        """Test successful install retrieval."""
        # Set up mock retriever
        mock_retriever = Mock()
        mock_docs = [Mock(), Mock()]
        mock_retriever.invoke.return_value = mock_docs
        RetrieverTools.install_retriever = mock_retriever

        # Mock format_docs return value
        formatted_result = ("formatted_text", ["source1"], ["url1"], ["context1"])
        mock_format_docs.return_value = formatted_result

        result = RetrieverTools.retrieve_install("test query")

        assert result == formatted_result
        mock_retriever.invoke.assert_called_once_with(input="test query")
        mock_format_docs.assert_called_once_with(mock_docs)

    def test_retrieve_install_not_initialized(self):
        """Test install retrieval when retriever not initialized."""
        RetrieverTools.install_retriever = None

        with pytest.raises(ValueError, match="Install Retriever not initialized"):
            RetrieverTools.retrieve_install("test query")

    @patch("src.agents.retriever_tools.format_docs")
    def test_retrieve_errinfo_success(self, mock_format_docs):
        """Test successful error info retrieval."""
        # Set up mock retriever
        mock_retriever = Mock()
        mock_docs = [Mock(), Mock()]
        mock_retriever.invoke.return_value = mock_docs
        RetrieverTools.errinfo_retriever = mock_retriever

        # Mock format_docs return value
        formatted_result = ("formatted_text", ["source1"], ["url1"], ["context1"])
        mock_format_docs.return_value = formatted_result

        result = RetrieverTools.retrieve_errinfo("test query")

        assert result == formatted_result
        mock_retriever.invoke.assert_called_once_with(input="test query")
        mock_format_docs.assert_called_once_with(mock_docs)

    def test_retrieve_errinfo_not_initialized(self):
        """Test error info retrieval when retriever not initialized."""
        RetrieverTools.errinfo_retriever = None

        with pytest.raises(ValueError, match="Error Info Retriever not initialized"):
            RetrieverTools.retrieve_errinfo("test query")

    @patch("src.agents.retriever_tools.format_docs")
    def test_retrieve_yosys_rtdocs_success(self, mock_format_docs):
        """Test successful Yosys RTDocs retrieval."""
        # Set up mock retriever
        mock_retriever = Mock()
        mock_docs = [Mock(), Mock()]
        mock_retriever.invoke.return_value = mock_docs
        RetrieverTools.yosys_rtdocs_retriever = mock_retriever

        # Mock format_docs return value
        formatted_result = ("formatted_text", ["source1"], ["url1"], ["context1"])
        mock_format_docs.return_value = formatted_result

        result = RetrieverTools.retrieve_yosys_rtdocs("test query")

        assert result == formatted_result
        mock_retriever.invoke.assert_called_once_with(input="test query")
        mock_format_docs.assert_called_once_with(mock_docs)

    def test_retrieve_yosys_rtdocs_not_initialized(self):
        """Test Yosys RTDocs retrieval when retriever not initialized."""
        RetrieverTools.yosys_rtdocs_retriever = None

        with pytest.raises(ValueError, match="Yosys RTDocs Retriever not initialized"):
            RetrieverTools.retrieve_yosys_rtdocs("test query")

    @patch("src.agents.retriever_tools.format_docs")
    def test_retrieve_klayout_docs_success(self, mock_format_docs):
        """Test successful KLayout docs retrieval."""
        # Set up mock retriever
        mock_retriever = Mock()
        mock_docs = [Mock(), Mock()]
        mock_retriever.invoke.return_value = mock_docs
        RetrieverTools.klayout_retriever = mock_retriever

        # Mock format_docs return value
        formatted_result = ("formatted_text", ["source1"], ["url1"], ["context1"])
        mock_format_docs.return_value = formatted_result

        result = RetrieverTools.retrieve_klayout_docs("test query")

        assert result == formatted_result
        mock_retriever.invoke.assert_called_once_with(input="test query")
        mock_format_docs.assert_called_once_with(mock_docs)

    def test_retrieve_klayout_docs_not_initialized(self):
        """Test KLayout docs retrieval when retriever not initialized."""
        RetrieverTools.klayout_retriever = None

        with pytest.raises(ValueError, match="KLayout Retriever not initialized"):
            RetrieverTools.retrieve_klayout_docs("test query")

    @patch("src.agents.retriever_tools.HybridRetrieverChain")
    def test_initialize_verifies_configuration_parameters(self, mock_hybrid_chain):
        """Test that initialize passes correct configuration parameters."""
        tools = RetrieverTools()

        # Mock the HybridRetrieverChain instances
        mock_chains = []
        for i in range(6):
            mock_chain = Mock()
            mock_chain.retriever = Mock()
            mock_chains.append(mock_chain)

        mock_hybrid_chain.side_effect = mock_chains

        embeddings_config = {"type": "GOOGLE_GENAI", "name": "embedding-model"}
        reranking_model_name = "cross-encoder-model"

        tools.initialize(
            embeddings_config=embeddings_config,
            reranking_model_name=reranking_model_name,
            use_cuda=True,
            fast_mode=False,
        )

        # Verify all chain initializations received correct config
        for call in mock_hybrid_chain.call_args_list:
            kwargs = call[1]
            assert kwargs["embeddings_config"] == embeddings_config
            assert kwargs["reranking_model_name"] == reranking_model_name
            assert kwargs["use_cuda"] is True
            assert kwargs["weights"] == [0.6, 0.2, 0.2]
            assert kwargs["contextual_rerank"] is True

    @patch("src.agents.retriever_tools.HybridRetrieverChain")
    def test_initialize_with_environment_variables(self, mock_hybrid_chain):
        """Test initialization respects environment variables."""
        tools = RetrieverTools()

        # Mock the HybridRetrieverChain instances
        mock_chains = []
        for i in range(6):
            mock_chain = Mock()
            mock_chain.retriever = Mock()
            mock_chains.append(mock_chain)

        mock_hybrid_chain.side_effect = mock_chains

        # Mock environment variables
        with patch("src.agents.retriever_tools.search_k", 15):
            with patch("src.agents.retriever_tools.chunk_size", 2000):
                tools.initialize(
                    embeddings_config={"type": "HF", "name": "test-model"},
                    reranking_model_name="test-reranker",
                    use_cuda=False,
                    fast_mode=False,
                )

                # Verify search_k and chunk_size are used
                for call in mock_hybrid_chain.call_args_list:
                    kwargs = call[1]
                    assert kwargs["search_k"] == 15
                    assert kwargs["chunk_size"] == 2000

    def test_tool_decorators_applied(self):
        """Test that all retrieve methods have @tool decorators."""
        # Verify that the tool decorators create StructuredTool objects
        assert hasattr(RetrieverTools.retrieve_general, "name")
        assert hasattr(RetrieverTools.retrieve_cmds, "name")
        assert hasattr(RetrieverTools.retrieve_install, "name")
        assert hasattr(RetrieverTools.retrieve_errinfo, "name")
        assert hasattr(RetrieverTools.retrieve_yosys_rtdocs, "name")
        assert hasattr(RetrieverTools.retrieve_klayout_docs, "name")

    @patch("src.agents.retriever_tools.HybridRetrieverChain")
    def test_different_docs_paths_for_retrievers(self, mock_hybrid_chain):
        """Test that different retrievers use different document paths."""
        tools = RetrieverTools()

        # Mock the HybridRetrieverChain instances
        mock_chains = []
        for i in range(6):
            mock_chain = Mock()
            mock_chain.retriever = Mock()
            mock_chains.append(mock_chain)

        mock_hybrid_chain.side_effect = mock_chains

        tools.initialize(
            embeddings_config={"type": "HF", "name": "test-model"},
            reranking_model_name="test-reranker",
            use_cuda=False,
            fast_mode=False,
        )

        # Verify different markdown_docs_path for different retrievers
        general_call = mock_hybrid_chain.call_args_list[0]
        install_call = mock_hybrid_chain.call_args_list[1]
        commands_call = mock_hybrid_chain.call_args_list[2]
        errinfo_call = mock_hybrid_chain.call_args_list[5]

        general_paths = general_call[1]["markdown_docs_path"]
        install_paths = install_call[1]["markdown_docs_path"]
        commands_paths = commands_call[1]["markdown_docs_path"]
        errinfo_paths = errinfo_call[1]["markdown_docs_path"]

        # Each retriever should have different document paths
        assert general_paths != install_paths
        assert install_paths != commands_paths
        assert commands_paths != errinfo_paths

        # Install should have installation-specific paths
        assert any("installation" in path for path in install_paths)

        # Commands should have tools-specific paths
        assert any("tools" in path for path in commands_paths)

        # Errinfo should have error-specific paths
        assert any("man3" in path for path in errinfo_paths)

    @patch("src.agents.retriever_tools.HybridRetrieverChain")
    def test_html_docs_configuration(self, mock_hybrid_chain):
        """Test HTML docs configuration for specific retrievers."""
        tools = RetrieverTools()

        # Mock the HybridRetrieverChain instances
        mock_chains = []
        for i in range(6):
            mock_chain = Mock()
            mock_chain.retriever = Mock()
            mock_chains.append(mock_chain)

        mock_hybrid_chain.side_effect = mock_chains

        tools.initialize(
            embeddings_config={"type": "HF", "name": "test-model"},
            reranking_model_name="test-reranker",
            use_cuda=False,
            fast_mode=False,
        )

        # Check Yosys retriever has HTML docs
        yosys_call = mock_hybrid_chain.call_args_list[3]
        yosys_html_paths = yosys_call[1]["html_docs_path"]
        assert len(yosys_html_paths) > 0
        assert any("yosys" in path for path in yosys_html_paths)

        # Check KLayout retriever has HTML docs
        klayout_call = mock_hybrid_chain.call_args_list[4]
        klayout_html_paths = klayout_call[1]["html_docs_path"]
        assert len(klayout_html_paths) > 0
        assert any("klayout" in path for path in klayout_html_paths)

    def test_environment_variable_defaults(self):
        """Test environment variable defaults."""
        # Test that the module has the expected constants
        from src.agents.retriever_tools import search_k, chunk_size

        # Should have default values or environment-loaded values
        assert isinstance(search_k, int)
        assert isinstance(chunk_size, int)
        assert search_k > 0
        assert chunk_size > 0

    def test_staticmethod_decorators(self):
        """Test that all retrieve methods are static methods."""
        # Check that the methods can be called without instance
        RetrieverTools.general_retriever = Mock()
        RetrieverTools.general_retriever.invoke.return_value = []

        with patch("src.agents.retriever_tools.format_docs") as mock_format:
            mock_format.return_value = ("", [], [], [])

            # Should be able to call without creating instance
            result = RetrieverTools.retrieve_general("test")
            assert result == ("", [], [], [])

    @patch("src.agents.retriever_tools.HybridRetrieverChain")
    def test_retriever_chain_create_hybrid_retriever_called(self, mock_hybrid_chain):
        """Test that create_hybrid_retriever is called on all chains."""
        tools = RetrieverTools()

        # Mock the HybridRetrieverChain instances
        mock_chains = []
        for i in range(6):
            mock_chain = Mock()
            mock_chain.retriever = Mock()
            mock_chain.create_hybrid_retriever = Mock()
            mock_chains.append(mock_chain)

        mock_hybrid_chain.side_effect = mock_chains

        tools.initialize(
            embeddings_config={"type": "HF", "name": "test-model"},
            reranking_model_name="test-reranker",
            use_cuda=False,
            fast_mode=False,
        )

        # Verify create_hybrid_retriever was called on all chains
        for mock_chain in mock_chains:
            mock_chain.create_hybrid_retriever.assert_called_once()

    def test_class_attributes_structure(self):
        """Test that class attributes have correct type annotations."""
        # Check that class has the expected attributes
        assert hasattr(RetrieverTools, "install_retriever")
        assert hasattr(RetrieverTools, "general_retriever")
        assert hasattr(RetrieverTools, "commands_retriever")
        assert hasattr(RetrieverTools, "errinfo_retriever")
        assert hasattr(RetrieverTools, "yosys_rtdocs_retriever")
        assert hasattr(RetrieverTools, "klayout_retriever")
        assert hasattr(RetrieverTools, "tool_descriptions")

        # tool_descriptions should be a string
        assert isinstance(RetrieverTools.tool_descriptions, str)
