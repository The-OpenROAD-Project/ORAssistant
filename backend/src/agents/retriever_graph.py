import os
import logging
from typing import Any, TypedDict, Annotated, Union, Optional

from langchain_core.messages import AnyMessage
from langchain_core.output_parsers import JsonOutputParser
from langchain_core.tools import BaseTool
from langgraph.graph import START, END, StateGraph
from langgraph.graph.graph import CompiledGraph
from langgraph.graph.message import add_messages
from langchain.tools.render import render_text_description
from langchain.prompts import ChatPromptTemplate
from langchain_google_vertexai import ChatVertexAI
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_ollama import ChatOllama

from .retriever_tools import RetrieverTools
from ..chains.base_chain import BaseChain
from ..prompts.prompt_templates import (
    summarise_prompt_template,
    tool_rephrase_prompt_template,
    rephrase_prompt_template,
)


logging.basicConfig(level=os.environ.get("LOGLEVEL", "INFO").upper())


class AgentState(TypedDict):
    messages: Annotated[list[AnyMessage], add_messages]
    context: Annotated[list[AnyMessage], add_messages]
    context_list: Annotated[list[str], add_messages]
    tools: list[str]
    sources: Annotated[list[str], add_messages]
    urls: Annotated[list[str], add_messages]
    chat_history: str


class ToolNode:
    def __init__(self, tool_fn: BaseTool) -> None:
        self.tool_fn = tool_fn

    def get_node(self, state: AgentState) -> dict[str, Any]:
        query = state["messages"][-1].content
        if query is None:
            raise ValueError("Query is None")

        response, sources, urls, context_list = self.tool_fn.invoke(query)  # type: ignore

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
        return {
            "context": response,
            "sources": sources,
            "urls": urls,
            "context_list": context_list,
        }


class RetrieverGraph:
    def __init__(
        self,
        llm_model: Union[ChatGoogleGenerativeAI, ChatVertexAI, ChatOllama],
        embeddings_config: dict[str, str],
        reranking_model_name: str,
        inbuilt_tool_calling: bool,
        use_cuda: bool = False,
        fast_mode: bool = False,
    ):
        self.llm = llm_model
        self.retriever_tools: RetrieverTools = RetrieverTools()
        self.retriever_tools.initialize(
            embeddings_config=embeddings_config,
            reranking_model_name=reranking_model_name,
            use_cuda=use_cuda,
            fast_mode=fast_mode,
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
        self.inbuilt_tool_calling = inbuilt_tool_calling

        self.tool_descriptions = ""
        for tool in self.tools:
            text_desc = render_text_description([tool])
            text_desc.replace("(query: str) -> Tuple[str, list[str], list[str]]", " ")
            self.tool_descriptions += text_desc + "\n\n"

        self.graph: Optional[CompiledGraph] = None
        self.llm_chain = BaseChain(
            llm_model=self.llm,
            prompt_template_str=summarise_prompt_template,
        ).get_llm_chain()

    def agent(self, state: AgentState) -> dict[str, list[str]]:
        followup_question = state["messages"][-1].content

        if self.llm is None:
            return {"tools": []}

        if self.inbuilt_tool_calling:
            model = self.llm.bind_tools(self.tools, tool_choice="any")  # type: ignore

            tool_choice_chain = (
                ChatPromptTemplate.from_template(rephrase_prompt_template)
                | self.llm
                | JsonOutputParser()
            )
            response = tool_choice_chain.invoke(
                {
                    "question": followup_question,
                    "chat_history": state["chat_history"],
                }
            )

            response = model.invoke(followup_question)

            if response is None or response.tool_calls is None:
                return {"tools": []}

            return {"tools": response.tool_calls}

        else:
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
                logging.warning("Tool selection failed. Returning empty tool list.")

            if "rephrased_question" in str(response):
                state["messages"][-1].content = response.get("rephrased_question")
            else:
                logging.warning("Rephrased question not found in response.")

            return {"tools": tool_calls}

    def generate(self, state: AgentState) -> dict[str, Any]:
        query = state["messages"][-1].content
        context = state["context"][-1].content
        print("state keys", state.keys())

        ans = self.llm_chain.invoke({"context": context, "question": query})

        if ans is not None:
            return {"messages": [ans]}

        return {"messages": []}

    def route(self, state: AgentState) -> list[str]:
        tools = state["tools"]

        if tools == []:
            return ["retrieve_general"]

        if self.inbuilt_tool_calling:
            tool_names = [tool["name"] for tool in tools if "name" in tool]  # type: ignore
            return tool_names
        else:
            return tools

    def initialize(self) -> None:
        workflow = StateGraph(AgentState)

        commands = ToolNode(self.retriever_tools.retrieve_cmds)
        install = ToolNode(self.retriever_tools.retrieve_install)
        general = ToolNode(self.retriever_tools.retrieve_general)
        klayout_docs = ToolNode(self.retriever_tools.retrieve_klayout_docs)
        errinfo = ToolNode(self.retriever_tools.retrieve_errinfo)
        yosys_rtdocs = ToolNode(self.retriever_tools.retrieve_yosys_rtdocs)

        workflow.add_node("agent", self.agent)
        workflow.add_node("generate", self.generate)

        workflow.add_node("retrieve_cmds", commands.get_node)
        workflow.add_node("retrieve_install", install.get_node)
        workflow.add_node("retrieve_general", general.get_node)
        workflow.add_node("retrieve_klayout_docs", klayout_docs.get_node)
        workflow.add_node("retrieve_errinfo", errinfo.get_node)
        workflow.add_node("retrieve_yosys_rtdocs", yosys_rtdocs.get_node)

        workflow.add_edge(START, "agent")
        workflow.add_conditional_edges(
            "agent",
            self.route,  # type: ignore
            [
                "retrieve_cmds",
                "retrieve_install",
                "retrieve_general",
                "retrieve_klayout_docs",
                "retrieve_errinfo",
                "retrieve_yosys_rtdocs",
            ],
        )

        workflow.add_edge("retrieve_cmds", "generate")
        workflow.add_edge("retrieve_install", "generate")
        workflow.add_edge("retrieve_general", "generate")
        workflow.add_edge("retrieve_klayout_docs", "generate")
        workflow.add_edge("retrieve_errinfo", "generate")
        workflow.add_edge("retrieve_yosys_rtdocs", "generate")

        workflow.add_edge("generate", END)

        self.graph = workflow.compile()

        return
