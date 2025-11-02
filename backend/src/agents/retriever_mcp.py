import logging
import asyncio
from typing import Any
from ..openroad_mcp.client.client import get_tools
from langgraph.graph import END
from .retriever_typing import AgentState
from langchain.prompts import ChatPromptTemplate
from ..prompts.prompt_templates import run_orfs_prompt_template
from langchain_core.tools.base import ToolException
from langchain_google_vertexai import ChatVertexAI
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_ollama import ChatOllama


class MCP:
    llm: ChatVertexAI | ChatGoogleGenerativeAI | ChatOllama
    workflow: Any

    # TODO: mcp breaks support for llms without toolchain i.e. json parsing
    def mcp_agent(self, state: AgentState) -> dict[str, list[Any]]:
        query = state["messages"][-1].content
        logging.info(query)
        custom_tools = get_tools()
        model = self.llm.bind_tools(custom_tools)

        run_orfs_chain = (
            ChatPromptTemplate.from_template(run_orfs_prompt_template) | model
        )
        response = run_orfs_chain.invoke(
            {
                "question": query,
                "chat_history": state["chat_history"],
            }
        )

        state["mcp_response"] = [response]  # type: ignore
        return {"messages": [response]}

    # end of mcp_agent
    def mcp_tools_condition(
        self,
        state: AgentState,
        messages_key: str = "messages",
    ) -> str:
        if isinstance(state, list):
            ai_message = state[-1]
        elif isinstance(state, dict) and (messages := state.get(messages_key, [])):
            ai_message = messages[-1] if messages else None  # type: ignore
        elif hasattr(state, messages_key) and (
            messages := getattr(state, messages_key, [])
        ):
            ai_message = messages[-1] if messages else None
        else:
            ai_message = state["messages"][-1] if state.get("messages") else None

        if ai_message is None:
            raise ValueError(f"No messages found in input state to tool_edge: {state}")
        logging.info(f"state: {state}")
        # ai_message = state["message"]
        if hasattr(ai_message, "tool_calls") and len(ai_message.tool_calls) > 0:
            return "mcp_tools"
        # return "__end__"

        return "mcp_tools"

    # end of mcp_tools_condition
    def mcp_tool_node(self, state: AgentState) -> dict[str, list[Any]]:
        custom_tools = get_tools()
        tools_by_name = {tool.name: tool for tool in custom_tools}
        tool_calls = getattr(state["messages"][-1], "tool_calls", [])
        logging.info(tool_calls)
        result: list[Any] = []
        for tool_call in tool_calls:
            tool = tools_by_name[tool_call["name"]]
            logging.info(tool_call["args"])
            try:
                observation = asyncio.run(tool.ainvoke(tool_call["args"]))
                result.append(observation)
            except ToolException as e:
                error_msg = f"Tool '{tool_call['name']}' failed: {str(e)}"
                logging.error(f"ToolException during {tool_call['name']}: {e}")
                result.append(error_msg)
            except Exception as e:
                error_msg = f"Tool '{tool_call['name']}' encountered an error: {str(e)}"
                logging.error(f"Unexpected error during {tool_call['name']}: {e}")
                result.append(error_msg)

        logging.info("DONE")
        logging.info(result)
        return {"messages": result}

    # end of mcp_tools_condition
    def mcp_workflow(self) -> None:
        self.workflow.add_node("mcp_agent", self.mcp_agent)

        self.workflow.add_node("mcp_tools", self.mcp_tool_node)

        self.workflow.add_conditional_edges(
            "mcp_agent",
            self.mcp_tools_condition,
            {"mcp_tools": "mcp_tools"},
        )
        self.workflow.add_edge("mcp_tools", END)

    # end of mcp_workflow
