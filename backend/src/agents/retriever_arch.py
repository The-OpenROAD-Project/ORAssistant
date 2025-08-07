#!/usr/bin/env python3
import logging
from langgraph.graph import START, END, StateGraph
from .retriever_typing import AgentState

class Arch():
    def arch_agent(self, state: AgentState):
        logging.info("arch")
        return {"messages": []}
    def arch_workflow(self):
        self.workflow.add_node("arch_agent", self.arch_agent)

        self.workflow.add_edge("arch_agent", END)
