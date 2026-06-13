from src.agents.retriever_typing import AgentState


class TestAgentState:
    """Test suite for the AgentState TypedDict."""

    def test_agent_state_includes_context_list(self):
        """AgentState must declare context_list so LangGraph propagates it (issue #259).

        ToolNode.get_node returns a ``context_list`` key, but LangGraph drops any
        state key that is not declared on the graph's state schema. Without this
        annotation the retrieved context list is silently lost downstream.
        """
        assert "context_list" in AgentState.__annotations__
