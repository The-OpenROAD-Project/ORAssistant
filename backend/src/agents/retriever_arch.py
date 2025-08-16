import logging
from typing import Any
from langgraph.graph import END
from .retriever_typing import AgentState


class Arch:
    workflow: Any

    def arch_agent(self, state: AgentState) -> dict[str, list[Any]]:
        logging.info(f"arch agent called with {len(state['messages'])} messages")
        return {"messages": []}

    def arch_workflow(self) -> None:
        self.workflow.add_node("arch_agent", self.arch_agent)

        self.workflow.add_edge("arch_agent", END)
