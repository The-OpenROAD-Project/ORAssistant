"""Unit tests for the tools that parse_agent_output reports for a RAG run."""

from unittest.mock import Mock

from langchain_core.documents import Document
from langchain_core.messages import AIMessage

from src.agents.retriever_rag import ToolNode
from src.api.routers.conversations import parse_agent_output
from src.tools.format_docs import format_docs


def rag_graph_output(selected: list[str], executed: str) -> list[dict]:
    """Build the stream_mode="updates" output of one RAG run.

    rag_agent selects the tools in selected, and the graph runs only the
    executed node. The retrieve node output comes from the real ToolNode and
    format_docs, so the test sees the same keys and values as the live graph.
    """
    docs = [
        Document(
            page_content="Chunk about placement.",
            metadata={"source": "place.md", "url": "https://example.com/place"},
        )
    ]
    retriever_tool = Mock()
    retriever_tool.invoke.return_value = format_docs(docs)
    retrieve_output = ToolNode(retriever_tool).get_node(
        {"messages": [Mock(content="query")]}
    )
    tool_calls = [
        {"name": name, "args": {"query": "query"}, "id": name, "type": "tool_call"}
        for name in selected
    ]

    return [
        {"classify": {"agent_type": ["rag_agent"]}},
        {"rag_agent": {"tools": tool_calls}},
        {executed: retrieve_output},
        {"rag_generate": {"messages": [AIMessage(content="answer")]}},
    ]


class TestRagTools:
    """Test suite for the RAG tools in parse_agent_output."""

    def test_reports_the_executed_retrieval_node(self):
        output = rag_graph_output(["retrieve_cmds"], "retrieve_cmds")

        _, _, tools = parse_agent_output(output)

        assert tools == ["retrieve_cmds"]

    def test_reports_only_the_node_that_ran(self):
        """rag_route runs only the first selected tool, so report only that."""
        output = rag_graph_output(
            ["retrieve_install", "retrieve_general"], "retrieve_install"
        )

        _, _, tools = parse_agent_output(output)

        assert tools == ["retrieve_install"]

    def test_reports_the_fallback_node_when_no_tool_was_selected(self):
        output = rag_graph_output([], "retrieve_general")

        _, _, tools = parse_agent_output(output)

        assert tools == ["retrieve_general"]
