import pytest
from unittest.mock import Mock, patch

from langchain_core.messages import AIMessage
from langchain_core.runnables import RunnableLambda

from src.agents.retriever_graph import RetrieverGraph
from src.agents.retriever_rag import ToolNode


class TestToolNode:
    """Test suite for ToolNode class."""

    def test_init(self):
        """Test ToolNode initialization."""
        mock_tool = Mock()
        node = ToolNode(mock_tool)

        assert node.tool_fn == mock_tool

    def test_get_node_with_valid_query(self):
        """Test get_node with valid query."""
        mock_tool = Mock()
        mock_tool.invoke.return_value = (
            ["response1", "response2"],
            ["source1", "source2"],
            ["url1", "url2"],
            ["context1", "context2"],
        )

        node = ToolNode(mock_tool)

        # Create mock message
        mock_message = Mock()
        mock_message.content = "test query"

        state = {
            "messages": [mock_message],
            "context": [],
            "context_list": [],
            "tools": [],
            "sources": [],
            "urls": [],
            "chat_history": "",
        }

        result = node.get_node(state)

        assert result["context"] == ["response1", "response2"]
        assert result["sources"] == ["source1", "source2"]
        assert result["urls"] == ["url1", "url2"]
        assert result["context_list"] == ["context1", "context2"]
        mock_tool.invoke.assert_called_once_with("test query")

    def test_get_node_with_none_query(self):
        """Test get_node with None query raises ValueError."""
        mock_tool = Mock()
        node = ToolNode(mock_tool)

        # Create mock message with None content
        mock_message = Mock()
        mock_message.content = None

        state = {
            "messages": [mock_message],
            "context": [],
            "context_list": [],
            "tools": [],
            "sources": [],
            "urls": [],
            "chat_history": "",
        }

        with pytest.raises(ValueError, match="Query is None"):
            node.get_node(state)


class TestRetrieverGraph:
    """Test suite for RetrieverGraph class."""

    @patch("src.agents.retriever_rag.RetrieverTools")
    @patch("src.agents.retriever_graph.BaseChain")
    def test_init(self, mock_base_chain, mock_retriever_tools):
        """Test RetrieverGraph initialization."""
        mock_llm = Mock()
        embeddings_config = {"type": "HF", "name": "test-model"}
        reranking_model_name = "test-reranker"

        # Mock the BaseChain and its methods
        mock_chain_instance = Mock()
        mock_base_chain.return_value = mock_chain_instance
        mock_chain_instance.get_llm_chain.return_value = Mock()

        # Mock the RetrieverTools
        mock_tools_instance = Mock()
        mock_retriever_tools.return_value = mock_tools_instance

        # Create mock tools
        mock_tools_instance.retrieve_cmds = Mock()
        mock_tools_instance.retrieve_install = Mock()
        mock_tools_instance.retrieve_general = Mock()
        mock_tools_instance.retrieve_klayout_docs = Mock()
        mock_tools_instance.retrieve_errinfo = Mock()
        mock_tools_instance.retrieve_yosys_rtdocs = Mock()

        graph = RetrieverGraph(
            llm_model=mock_llm,
            embeddings_config=embeddings_config,
            reranking_model_name=reranking_model_name,
            inbuilt_tool_calling=True,
            use_cuda=True,
            fast_mode=True,
        )

        assert graph.llm == mock_llm
        assert graph.inbuilt_tool_calling is True
        assert graph.graph is None
        assert len(graph.tools) == 6
        assert len(graph.tool_names) == 6
        assert "retrieve_cmds" in graph.tool_names
        assert "retrieve_install" in graph.tool_names
        assert "retrieve_general" in graph.tool_names

    @patch("src.agents.retriever_rag.RetrieverTools")
    @patch("src.agents.retriever_graph.BaseChain")
    def test_agent_with_none_llm(self, mock_base_chain, mock_retriever_tools):
        """Test agent method with None LLM."""
        # Mock the BaseChain
        mock_chain_instance = Mock()
        mock_base_chain.return_value = mock_chain_instance
        mock_chain_instance.get_llm_chain.return_value = Mock()

        # Mock the RetrieverTools
        mock_tools_instance = Mock()
        mock_retriever_tools.return_value = mock_tools_instance

        # Create mock tools
        mock_tools_instance.retrieve_cmds = Mock()
        mock_tools_instance.retrieve_install = Mock()
        mock_tools_instance.retrieve_general = Mock()
        mock_tools_instance.retrieve_klayout_docs = Mock()
        mock_tools_instance.retrieve_errinfo = Mock()
        mock_tools_instance.retrieve_yosys_rtdocs = Mock()

        graph = RetrieverGraph(
            llm_model=None,
            embeddings_config={"type": "HF", "name": "test-model"},
            reranking_model_name="test-reranker",
            inbuilt_tool_calling=False,
        )

        # Create mock message
        mock_message = Mock()
        mock_message.content = "test query"

        state = {
            "messages": [mock_message],
            "context": [],
            "context_list": [],
            "tools": [],
            "sources": [],
            "urls": [],
            "chat_history": "previous chat",
        }

        result = graph.rag_agent(state)

        assert result["tools"] == []

    @patch("src.agents.retriever_rag.RetrieverTools")
    @patch("src.agents.retriever_graph.BaseChain")
    def test_route_with_empty_tools(self, mock_base_chain, mock_retriever_tools):
        """Test route method with empty tools."""
        mock_llm = Mock()
        embeddings_config = {"type": "HF", "name": "test-model"}

        # Mock the BaseChain
        mock_chain_instance = Mock()
        mock_base_chain.return_value = mock_chain_instance
        mock_chain_instance.get_llm_chain.return_value = Mock()

        # Mock the RetrieverTools
        mock_tools_instance = Mock()
        mock_retriever_tools.return_value = mock_tools_instance

        # Create mock tools
        mock_tools_instance.retrieve_cmds = Mock()
        mock_tools_instance.retrieve_install = Mock()
        mock_tools_instance.retrieve_general = Mock()
        mock_tools_instance.retrieve_klayout_docs = Mock()
        mock_tools_instance.retrieve_errinfo = Mock()
        mock_tools_instance.retrieve_yosys_rtdocs = Mock()

        graph = RetrieverGraph(
            llm_model=mock_llm,
            embeddings_config=embeddings_config,
            reranking_model_name="test-reranker",
            inbuilt_tool_calling=False,
        )

        state = {
            "messages": [],
            "context": [],
            "context_list": [],
            "tools": [],
            "sources": [],
            "urls": [],
            "chat_history": "",
        }

        result = graph.rag_route(state)

        assert result == "retrieve_general"


class TestRagAgentToolSelection:
    """Test suite for the non-inbuilt-tool-calling branch of RAG.rag_agent."""

    def _make_graph(self, fake_llm: RunnableLambda) -> RetrieverGraph:
        with (
            patch("src.agents.retriever_rag.RetrieverTools") as mock_retriever_tools,
            patch("src.agents.retriever_graph.BaseChain") as mock_base_chain,
        ):
            mock_chain_instance = Mock()
            mock_base_chain.return_value = mock_chain_instance
            mock_chain_instance.get_llm_chain.return_value = Mock()

            mock_tools_instance = Mock()
            mock_retriever_tools.return_value = mock_tools_instance
            mock_tools_instance.retrieve_cmds = Mock()
            mock_tools_instance.retrieve_install = Mock()
            mock_tools_instance.retrieve_general = Mock()
            mock_tools_instance.retrieve_klayout_docs = Mock()
            mock_tools_instance.retrieve_errinfo = Mock()
            mock_tools_instance.retrieve_yosys_rtdocs = Mock()

            return RetrieverGraph(
                llm_model=fake_llm,
                embeddings_config={"type": "HF", "name": "test-model"},
                reranking_model_name="test-reranker",
                inbuilt_tool_calling=False,
            )

    def _make_state(self) -> dict:
        mock_message = Mock()
        mock_message.content = "test query"
        return {
            "messages": [mock_message],
            "context": [],
            "context_list": [],
            "tools": [],
            "sources": [],
            "urls": [],
            "chat_history": "",
        }

    def test_rag_agent_missing_tool_names_does_not_crash(self):
        """Regression test: a response without "tool_names" must not raise
        UnboundLocalError on `tool_calls` (issue #243, bug 1)."""
        fake_llm = RunnableLambda(lambda _: AIMessage(content='{"foo": "bar"}'))
        graph = self._make_graph(fake_llm)

        result = graph.rag_agent(self._make_state())

        assert result == {"tools": []}

    def test_rag_agent_filters_all_invalid_tool_names(self):
        """Regression test: filtering invalid tool names must not mutate the
        list while iterating over it, which previously skipped entries
        (issue #243, bug 1)."""
        fake_llm = RunnableLambda(
            lambda _: AIMessage(
                content='{"tool_names": ["invalid1", "invalid2", "retrieve_cmds"]}'
            )
        )
        graph = self._make_graph(fake_llm)

        result = graph.rag_agent(self._make_state())

        assert result == {"tools": ["retrieve_cmds"]}

    def test_tool_descriptions_have_type_signature_stripped(self):
        """Regression test: str.replace() result must be assigned back so the
        noisy type signature is actually removed (issue #243, bug 3)."""
        fake_llm = RunnableLambda(lambda _: AIMessage(content="{}"))

        with patch(
            "src.agents.retriever_rag.render_text_description",
            return_value="retrieve_cmds(query: str) -> Tuple[str, list[str], list[str]] - desc",
        ):
            graph = self._make_graph(fake_llm)

        assert (
            "(query: str) -> Tuple[str, list[str], list[str]]"
            not in graph.tool_descriptions
        )
