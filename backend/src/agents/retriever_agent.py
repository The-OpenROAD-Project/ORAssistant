from dotenv import load_dotenv

from src.tools.format_docs import format_docs
from src.prompts.answer_prompts import summarise_prompt_template
from src.chains.hybrid_retriever_chain import HybridRetrieverChain
from src.chains.similarity_retriever_chain import SimilarityRetrieverChain

from langchain_core.tools import tool

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_google_vertexai import ChatVertexAI
from langgraph.graph import MessagesState
from src.chains.base_chain import BaseChain
from langchain_core.tools import tool
from typing import Annotated, Any, Tuple


class ToolNode:
    def __init__(self, tool_fn):
        self.tool_fn = tool_fn

    def get_node(self, state):
        query = state["messages"][-1].content
        response, sources = self.tool_fn(query)
        return {"context": [response], "sources": sources}


class RetrieverAgent:
    def __init__(self, llm):
        self.llm = llm
        self.install_retriever = None
        self.cmds_retriever = None
        self.general_retriever = None

    @tool
    def retrieve_general(self, query: str) -> Tuple[str, list]:
        """
        Retrieve any general information related to OpenROAD and OpenROAD-flow-scripts
        """
        docs = self.general_retriever.invoke(input=query)
        print(len(docs))
        doc_text = ""
        doc_srcs = []

        for doc in docs:
            doc_text += f"\n\n- - - - - - - - - - - - - - - \n\n"
            doc_text += doc.page_content

            if "url" in doc.metadata:
                doc_srcs.append(doc.metadata["url"])
            elif "source" in doc.metadata:
                doc_srcs.append(doc.metadata["source"])

        return doc_text, doc_srcs

    @tool
    def retrieve_cmds(self, query: str) -> Tuple[str, list]:
        """
        Retrieve information related to the commands and tools in OpenROAD and OpenROAD-flow-scripts
        """
        docs = self.cmds_retriever.invoke(input=query)
        doc_text = ""
        doc_srcs = []
        for doc in docs:
            doc_text += f"\n\n- - - - - - - - - - - - - - - \n\n"
            doc_text += doc.page_content

            if "url" in doc.metadata:
                doc_srcs.append(doc.metadata["url"])
            elif "source" in doc.metadata:
                doc_srcs.append(doc.metadata["source"])

        return doc_text, doc_srcs

    @tool
    def retrieve_install(self, query: str) -> Tuple[str, list]:
        """
        Retrieve information related to the installation of OpenROAD and OpenROAD-flow-scripts
        """
        docs = self.install_retriever.invoke(input=query)
        doc_text = ""
        doc_srcs = []
        for doc in docs:
            doc_text += f"\n\n- - - - - - - - - - - - - - - \n\n"
            doc_text += doc.page_content

            if "url" in doc.metadata:
                doc_srcs.append(doc.metadata["url"])
            elif "source" in doc.metadata:
                doc_srcs.append(doc.metadata["source"])

        return doc_text, doc_srcs

    def initialize(self):
        install_retriever_chain = HybridRetrieverChain(
            embeddings_model_name="thenlper/gte-large",
            reranking_model_name="BAAI/bge-reranker-base",
            use_cuda=True,
            docs_path=[
                "./data/markdown/ORFS_docs/installation",
                "./data/markdown/OR_docs/installation",
            ],
            contextual_rerank=True,
            search_k=10,
        )
        install_retriever_chain.create_hybrid_retriever()
        self.install_retriever = install_retriever_chain.retriever

        cmds_retriever_chain = HybridRetrieverChain(
            embeddings_model_name="thenlper/gte-large",
            reranking_model_name="BAAI/bge-reranker-base",
            use_cuda=True,
            docs_path=["./data/markdown/OR_docs/tools"],
            manpages_path=["./data/markdown/manpages"],
            contextual_rerank=True,
            search_k=10,
        )
        cmds_retriever_chain.create_hybrid_retriever()
        self.cmds_retriever_chain = cmds_retriever_chain.retriever

        general_retriever_chain = HybridRetrieverChain(
            embeddings_model_name="thenlper/gte-large",
            reranking_model_name="BAAI/bge-reranker-base",
            use_cuda=True,
            docs_path=["./data/markdown/ORFS_docs", "./data/markdown/OR_docs"],
            manpages_path=["./data/markdown/manpages"],
            contextual_rerank=True,
            search_k=10,
        )
        general_retriever_chain.create_hybrid_retriever()
        self.general_retriever = general_retriever_chain.retriever

        self.tools = [self.retrieve_general, self.retrieve_cmds, self.retrieve_install]

        return
