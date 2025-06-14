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

from .retriever_typing import AgentState
from .retriever_tools import RetrieverTools
from ..chains.base_chain import BaseChain
from ..prompts.prompt_templates import (
    summarise_prompt_template,
    tool_rephrase_prompt_template,
    rephrase_prompt_template,
    classify_prompt_template
)

from .retriever_rag import RAG
from .retriever_mcp import MCP
from .retriever_arch import Arch

logging.basicConfig(level=os.environ.get("LOGLEVEL", "INFO").upper())


class RetrieverGraph(RAG, MCP, Arch):
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
        self.embeddings_config = embeddings_config
        self.reranking_model_name = reranking_model_name
        self.inbuilt_tool_calling = inbuilt_tool_calling
        self.use_cuda = use_cuda

        self.rag_initialize()

        self.graph: Optional[CompiledGraph] = None
        self.llm_chain = BaseChain(
            llm_model=self.llm,
            prompt_template_str=summarise_prompt_template,
        ).get_llm_chain()

        self.workflow = None

    def classify(self, state: AgentState) -> None:
        """Determine if architecture/config, execute, or RAG. Handle misc."""
        logging.info("classify task")

        classify_chain = (
            ChatPromptTemplate.from_template(classify_prompt_template)
            | self.llm
        )
        question = state["messages"][-1].content
        logging.info(question)
        response = classify_chain.invoke(
            {
                "question": question,
            }
        )

        logging.info(response.content)
        return {"agent_type": response.content}

    def fork_route(self, state: AgentState) -> list[str]:
        tmp = state["agent_type"]
        return tmp

    def initialize(self) -> None:
        self.workflow = StateGraph(AgentState)

        self.workflow.add_node("classify", self.classify)
        self.workflow.add_edge(START, "classify")
        self.workflow.add_conditional_edges(
            "classify",
            self.fork_route,
            [
                "rag_agent",
                "mcp_agent",
                "arch_agent",
            ],
        )

        self.rag_agent_workflow()
        self.mcp_workflow()
        self.arch_workflow()

        self.graph = self.workflow.compile()

        return
