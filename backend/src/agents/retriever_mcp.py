#!/usr/bin/env python3
import logging
import asyncio
from ..openroad_mcp.client.client import tools as custom_tools
from langgraph.graph import START, END, StateGraph
from .retriever_typing import AgentState
from langchain.prompts import ChatPromptTemplate
from ..prompts.prompt_templates import run_orfs_prompt_template
from langchain_core.tools.base import ToolException

class MCP:
    # TODO: mcp breaks support for llms without toolchain i.e. json parsing
    def mcp_agent(self, state: AgentState):
        query = state["messages"][-1].content
        logging.info(query)
        model = self.llm.bind_tools(custom_tools)

        run_orfs_chain = (
            ChatPromptTemplate.from_template(run_orfs_prompt_template)
            | model
        )
        response = run_orfs_chain.invoke(
            {
                "question": query,
                "chat_history": state["chat_history"],
            }
        )

        state["mcp_response"] = [response]
        return {"messages": [response]}
    ### end of mcp_agent
    def mcp_tools_condition(self,
        state: AgentState,
        messages_key: str = "messages",
    ) -> list[str]:
        query = state["messages"][-1].content
        if isinstance(state, list):
            ai_message = state[-1]
        elif isinstance(state, dict) and (messages := state.get(messages_key, [])):
            ai_message = messages[-1]
        elif messages := getattr(state, messages_key, []):
            ai_message = messages[-1]
        else:
            raise ValueError(f"No messages found in input state to tool_edge: {state}")
        logging.info(f"state: {state}")
        #ai_message = state["message"]
        if hasattr(ai_message, "tool_calls") and len(ai_message.tool_calls) > 0:
            return ["mcp_tools"]
        #return "__end__"

        return ["mcp_tools"]
    ### end of mcp_tools_condition
    def mcp_tool_node(self, state: AgentState) :
        tools_by_name = {tool.name: tool for tool in custom_tools}
        logging.info(state["messages"][-1].tool_calls)
        result = []
        for tool_call in state["messages"][-1].tool_calls:
            tool = tools_by_name[tool_call["name"]]
            logging.info(tool_call["args"])
            try:
                observation = asyncio.run(tool.ainvoke(tool_call["args"]))
            except ToolException:
                logging.info("command not found...")
                observation = None

            if observation:
                result.append(observation)
            else:
                result.append("no return")
        logging.info("DONE")
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
