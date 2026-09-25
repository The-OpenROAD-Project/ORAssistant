"""Unit tests for context sources parsed from the agent graph output."""

from unittest.mock import Mock

from langchain_core.documents import Document
from langchain_core.messages import AIMessage

from src.agents.retriever_rag import ToolNode
from src.api.routers.conversations import parse_agent_output
from src.tools.format_docs import format_docs


def rag_graph_output(docs: list[Document]) -> list[dict]:
    """Build the stream_mode="updates" output of one RAG run over docs.

    The retrieve node output comes from the real ToolNode and format_docs,
    so the test sees the same keys and values as the live graph.
    """
    retriever_tool = Mock()
    retriever_tool.invoke.return_value = format_docs(docs)
    node = ToolNode(retriever_tool)
    retrieve_output = node.get_node({"messages": [Mock(content="query")]})

    return [
        {"classify": {"agent_type": ["rag_agent"]}},
        {"rag_agent": {"tools": ["retrieve_general"]}},
        {"retrieve_general": retrieve_output},
        {"rag_generate": {"messages": [AIMessage(content="answer")]}},
    ]


class TestRagContextSources:
    """Test suite for RAG context sources in parse_agent_output."""

    def test_each_source_holds_its_own_chunk(self):
        """Each context source pairs one chunk's text with that chunk's URL."""
        docs = [
            Document(
                page_content="Chunk about placement.",
                metadata={"source": "place.md", "url": "https://example.com/place"},
            ),
            Document(
                page_content="Chunk about routing.",
                metadata={"source": "route.md", "url": "https://example.com/route"},
            ),
        ]

        _, context_sources, tools = parse_agent_output(rag_graph_output(docs))

        assert [(cs.source, cs.context) for cs in context_sources] == [
            ("https://example.com/place", "Chunk about placement."),
            ("https://example.com/route", "Chunk about routing."),
        ]
        assert tools == []
