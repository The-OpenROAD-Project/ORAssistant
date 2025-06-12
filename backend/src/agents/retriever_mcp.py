#!/usr/bin/env python3
import logging
import asyncio
from ..mcp.client.client import tools as custom_tools
from langgraph.graph import START, END, StateGraph
from .retriever_typing import AgentState

class MCP:
    def mcp_agent(self, state: AgentState):
        query = state["messages"][-1].content
        #context = state["context"][-1].content
        print(query)
        response = self.llm.bind_tools(custom_tools).invoke(query)
        print("type")
        input(type(response))
        state["mcp_response"] = [response]
        return {"messages": [response]}
    ### end of mcp_agent
    def mcp_tools_condition(self,
        state: AgentState,
        messages_key: str = "messages",
    ) -> list[str]:
        input(messages_key)
        query = state["messages"][-1].content
        if isinstance(state, list):
            ai_message = state[-1]
        elif isinstance(state, dict) and (messages := state.get(messages_key, [])):
            ai_message = messages[-1]
        elif messages := getattr(state, messages_key, []):
            ai_message = messages[-1]
        else:
            raise ValueError(f"No messages found in input state to tool_edge: {state}")
        print("state")
        input(state)
        #ai_message = state["message"]
        if hasattr(ai_message, "tool_calls") and len(ai_message.tool_calls) > 0:
            return "mcp_tools"
        #return "__end__"

        return ["mcp_tools"]
    ### end of mcp_tools_condition
    def mcp_tool_node(self, state: AgentState) :
        tools_by_name = {tool.name: tool for tool in custom_tools}
        print("beginning")
        input(state["messages"][-1].tool_calls)
        result = []
        for tool_call in state["messages"][-1].tool_calls:
            tool = tools_by_name[tool_call["name"]]
            print("what is type")
            input(type(tool))
            observation = asyncio.run(tool.ainvoke(tool_call["args"]))
            if observation:
                result.append(observation)
        print("DONE")
        logging.info(result)
        #return {"messages": result}
        return {"messages": result}
    ### end of mcp_tools_condition
    def mcp_workflow(self):
        self.workflow.add_node("mcp_agent", self.mcp_agent)

        self.workflow.add_node("mcp_tools", self.mcp_tool_node)

        self.workflow.add_conditional_edges(
            "mcp_agent",
            self.mcp_tools_condition, # goes to default_tools if matches
        )
        self.workflow.add_edge("mcp_tools", END)
    ### end of mcp_workflow
