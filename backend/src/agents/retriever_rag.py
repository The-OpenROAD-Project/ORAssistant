#!/usr/bin/env python3
import logging
from langchain_core.messages import AnyMessage
from langgraph.graph import START, END, StateGraph
from langchain_core.tools import BaseTool
from langchain.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from langchain.tools.render import render_text_description

from .retriever_typing import AgentState
from .retriever_tools import RetrieverTools
from ..prompts.prompt_templates import (
    summarise_prompt_template,
    tool_rephrase_prompt_template,
    rephrase_prompt_template,
)

class ToolNode:
    def __init__(self, tool_fn: BaseTool) -> None:
        self.tool_fn = tool_fn

    def get_node(self, state: AgentState) -> dict[str, list[str]]:
        query = state["messages"][-1].content
        if query is None:
            raise ValueError("Query is None")

        response, sources, urls = self.tool_fn.invoke(query)  # type: ignore

        if response != []:
            response = (
                [item for sublist in response for item in sublist]
                if isinstance(response[0], list)
                else response
            )
        if sources != []:
            sources = (
                [item for sublist in sources for item in sublist]
                if isinstance(sources[0], list)
                else sources
            )
        if urls != []:
            urls = (
                [item for sublist in urls for item in sublist]
                if isinstance(urls[0], list)
                else urls
            )
        return {"context": response, "sources": sources, "urls": urls}

class RAG:
    def rag_initialize(self, debug=False):
        self.retriever_tools: RetrieverTools = RetrieverTools()
        if not debug:
            self.retriever_tools.initialize(
                embeddings_config=self.embeddings_config,
                reranking_model_name=self.reranking_model_name,
                use_cuda=self.use_cuda,
            )

        self.tools = [
            self.retriever_tools.retrieve_cmds,
            self.retriever_tools.retrieve_install,
            self.retriever_tools.retrieve_general,
            self.retriever_tools.retrieve_klayout_docs,
            self.retriever_tools.retrieve_errinfo,
            self.retriever_tools.retrieve_yosys_rtdocs,
        ]
        self.tool_names = [
            "retrieve_cmds",
            "retrieve_install",
            "retrieve_general",
            "retrieve_klayout_docs",
            "retrieve_errinfo",
            "retrieve_yosys_rtdocs",
        ]

        self.tool_descriptions = ""
        for tool in self.tools:
            text_desc = render_text_description([tool])
            text_desc.replace("(query: str) -> Tuple[str, list[str], list[str]]", " ")
            self.tool_descriptions += text_desc + "\n\n"
    def rag_agent(self, state: AgentState) -> dict[str, list[str]]:
        followup_question = state["messages"][-1].content

        if self.llm is None:
            return {"tools": []}

       # TODO: delete this branch since inbuilt always false
       #if self.inbuilt_tool_calling:
       #    model = self.llm.bind_tools(self.tools, tool_choice="any")

       #    tool_choice_chain = (
       #        ChatPromptTemplate.from_template(rephrase_prompt_template)
       #        | self.llm
       #        | JsonOutputParser()
       #    )
       #    response = tool_choice_chain.invoke(
       #        {
       #            "question": followup_question,
       #            "chat_history": state["chat_history"],
       #        }
       #    )

       #    response = model.invoke(followup_question)

       #    if response is None or response.tool_calls is None:
       #        return {"tools": []}

       #    return {"tools": response.tool_calls}

       #else:
        tool_rephrase_chain = (
            ChatPromptTemplate.from_template(tool_rephrase_prompt_template)
            | self.llm
            | JsonOutputParser()
        )
        response = tool_rephrase_chain.invoke(
            {
                "question": followup_question,
                "tool_descriptions": self.tool_descriptions,
                "chat_history": state["chat_history"],
            }
        )

        if response is None:
            logging.warning(
                "Tool selection response not found. Returning empty tool list."
            )
            return {"tools": []}

        if "tool_names" in str(response):
            tool_calls = response.get("tool_names", [])
            for tool in tool_calls:
                if tool not in self.tool_names:
                    logging.warning(f"Tool {tool} not found in tool list.")
                    tool_calls.remove(tool)
        else:
            logging.warning(str(response))
            logging.warning("Tool selection failed. Returning empty tool list.")

        if "rephrased_question" in str(response):
            state["messages"][-1].content = response.get("rephrased_question")
        else:
            logging.warning("Rephrased question not found in response.")

        return {"tools": tool_calls}
    ### end of agent
    def rag_route(self, state: AgentState) -> list[str]:
        tools = state["tools"]

        if tools == []:
            return ["retrieve_general"]

       # TODO: delete
       #if self.inbuilt_tool_calling:
       #    tool_names = [tool["name"] for tool in tools if "name" in tool]  # type: ignore
       #    return tool_names
       #else:
        return tools
    ### end of route
    def rag_generate(self, state: AgentState) -> dict[str, list[AnyMessage]]:
        query = state["messages"][-1].content
        context = state["context"][-1].content

        ans = self.llm_chain.invoke({"context": context, "question": query})

        if ans is not None:
            return {"messages": [ans]}

        return {"messages": []}
    ### end of generate
    def rag_agent_workflow(self):
        # TODO: seperate tools into another class
        commands = ToolNode(self.retriever_tools.retrieve_cmds)
        install = ToolNode(self.retriever_tools.retrieve_install)
        general = ToolNode(self.retriever_tools.retrieve_general)
        klayout_docs = ToolNode(self.retriever_tools.retrieve_klayout_docs)
        errinfo = ToolNode(self.retriever_tools.retrieve_errinfo)
        yosys_rtdocs = ToolNode(self.retriever_tools.retrieve_yosys_rtdocs)

        self.workflow.add_node("retrieve_cmds", commands.get_node)
        self.workflow.add_node("retrieve_install", install.get_node)
        self.workflow.add_node("retrieve_general", general.get_node)
        self.workflow.add_node("retrieve_klayout_docs", klayout_docs.get_node)
        self.workflow.add_node("retrieve_errinfo", errinfo.get_node)
        self.workflow.add_node("retrieve_yosys_rtdocs", yosys_rtdocs.get_node)

        self.workflow.add_node("rag_agent", self.rag_agent)
        self.workflow.add_node("rag_generate", self.rag_generate)

        self.workflow.add_conditional_edges(
            "rag_agent",
            self.rag_route,  # type: ignore
            [
                "retrieve_cmds",
                "retrieve_install",
                "retrieve_general",
                "retrieve_klayout_docs",
                "retrieve_errinfo",
                "retrieve_yosys_rtdocs",
            ],
        )

        self.workflow.add_edge("retrieve_cmds", "rag_generate")
        self.workflow.add_edge("retrieve_install", "rag_generate")
        self.workflow.add_edge("retrieve_general", "rag_generate")
        self.workflow.add_edge("retrieve_klayout_docs", "rag_generate")
        self.workflow.add_edge("retrieve_errinfo", "rag_generate")
        self.workflow.add_edge("retrieve_yosys_rtdocs", "rag_generate")

        self.workflow.add_edge("rag_generate", END)
    ### end of agent_workflow
