import os
import logging
from typing import Optional

from langgraph.graph import START, StateGraph
from langgraph.graph.state import CompiledStateGraph
from langchain.prompts import ChatPromptTemplate
from langchain_google_vertexai import ChatVertexAI
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_ollama import ChatOllama

from .retriever_typing import AgentState
from .routing_tools import arch_info, mcp_info, rag_info
from ..chains.base_chain import BaseChain
from ..prompts.prompt_templates import (
    summarise_prompt_template,
    classify_prompt_template,
)
from .retriever_rag import RAG
from .retriever_mcp import MCP
from .retriever_arch import Arch

logging.basicConfig(level=os.environ.get("LOGLEVEL", "INFO").upper())


class RetrieverGraph(RAG, MCP, Arch):
    def __init__(
        self,
        llm_model: ChatGoogleGenerativeAI | ChatVertexAI | ChatOllama,
        embeddings_config: dict[str, str],
        reranking_model_name: str,
        inbuilt_tool_calling: bool,
        use_cuda: bool = False,
        fast_mode: bool = False,
        debug: bool = False,
        enable_mcp: bool = False,
    ):
        self.llm = llm_model
        self.embeddings_config = embeddings_config
        self.reranking_model_name = reranking_model_name
        self.inbuilt_tool_calling = inbuilt_tool_calling
        self.use_cuda = use_cuda
        self.fast_mode = fast_mode
        self.debug = debug
        self.enable_mcp = enable_mcp

        self.rag_initialize()

        self.graph: Optional[CompiledStateGraph] = None
        self.llm_chain = BaseChain(
            llm_model=self.llm,
            prompt_template_str=summarise_prompt_template,
        ).get_llm_chain()

        self.workflow = None

    def classify(self, state: AgentState) -> dict[str, list[str]]:
        """Determine if architecture/config, execute, or RAG. Handle misc."""
        if self.inbuilt_tool_calling and self.enable_mcp:
            question = state["messages"][-1].content
            model = self.llm.bind_tools(
                [rag_info, mcp_info, arch_info],  # type: ignore
                tool_choice="any",
            )

            classify_chain = (
                ChatPromptTemplate.from_template(classify_prompt_template) | model
            )
            response = classify_chain.invoke(
                {
                    "question": question,
                }
            )

            fork_lookup = {
                "rag_info": rag_info,
                "mcp_info": mcp_info,
                "arch_info": arch_info,
            }
            result = "rag_agent"
            for tool_call in response.tool_calls:  # type: ignore
                tool = fork_lookup[tool_call["name"]]
                result = tool.invoke(tool_call["args"])

            logging.info(result)
            return {"agent_type": [result]}
        elif self.inbuilt_tool_calling and not self.enable_mcp:
            # When MCP is disabled but inbuilt tool calling is enabled, just use RAG
            logging.info("MCP disabled, defaulting to RAG agent")
            return {"agent_type": ["rag_agent"]}
        else:
            logging.info("classify task")

            classify_chain = (
                ChatPromptTemplate.from_template(classify_prompt_template) | self.llm
            )
            question = state["messages"][-1].content
            logging.info(question)
            response = classify_chain.invoke(
                {
                    "question": question,
                }
            )

            logging.info(response.content)
            return {"agent_type": [response.content]}  # type: ignore

    def fork_route(self, state: AgentState) -> str:
        # TODO: if more than one agent add handler
        if not self.enable_mcp:
            tmp = "rag_agent"
        else:
            #tmp = state["agent_type"][0]
            tmp = "mcp_agent"
        return tmp

    def initialize(self) -> None:
        self.workflow = StateGraph(AgentState)

        self.workflow.add_node("classify", self.classify)
        self.workflow.add_edge(START, "classify")
        self.workflow.add_conditional_edges(
            "classify",
            self.fork_route,
            {
                "rag_agent": "rag_agent",
                "mcp_agent": "mcp_agent",
                "arch_agent": "arch_agent",
            },
        )

        self.rag_agent_workflow()
        self.mcp_workflow()
        self.arch_workflow()

        self.graph = self.workflow.compile()

        return
