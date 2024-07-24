from ..chains.hybrid_retriever_chain import HybridRetrieverChain

from langchain_core.tools import tool
from langchain.retrievers import EnsembleRetriever
from langchain.retrievers import ContextualCompressionRetriever

from typing import Tuple, Optional, Union


class RetrieverAgent:
    def __init__(self) -> None:
        pass

    install_retriever: Optional[
        Union[EnsembleRetriever, ContextualCompressionRetriever]
    ]
    general_retriever: Optional[
        Union[EnsembleRetriever, ContextualCompressionRetriever]
    ]
    opensta_retriever: Optional[
        Union[EnsembleRetriever, ContextualCompressionRetriever]
    ]
    commands_retriever: Optional[
        Union[EnsembleRetriever, ContextualCompressionRetriever]
    ]

    def initialize(
        self,
        embeddings_model_name: str,
        reranking_model_name: str,
        use_cuda: bool = False,
    ) -> None:
        opensta_retriever_chain = HybridRetrieverChain(
            embeddings_model_name=embeddings_model_name,
            reranking_model_name=reranking_model_name,
            use_cuda=use_cuda,
            other_docs_path=['./data/pdf/OpenSTA/OpenSTA_docs.pdf'],
            contextual_rerank=True,
            search_k=10,
        )
        opensta_retriever_chain.create_hybrid_retriever()
        RetrieverAgent.opensta_retriever = opensta_retriever_chain.retriever

        install_retriever_chain = HybridRetrieverChain(
            embeddings_model_name=embeddings_model_name,
            reranking_model_name=reranking_model_name,
            use_cuda=use_cuda,
            docs_path=[
                './data/markdown/ORFS_docs/installation',
                './data/markdown/OR_docs/installation',
            ],
            contextual_rerank=True,
            search_k=10,
        )
        install_retriever_chain.create_hybrid_retriever()
        RetrieverAgent.install_retriever = install_retriever_chain.retriever

        commands_retriever_chain = HybridRetrieverChain(
            embeddings_model_name=embeddings_model_name,
            reranking_model_name=reranking_model_name,
            use_cuda=use_cuda,
            docs_path=['./data/markdown/OR_docs/tools'],
            manpages_path=['./data/markdown/manpages'],
            contextual_rerank=True,
            search_k=10,
        )
        commands_retriever_chain.create_hybrid_retriever()
        RetrieverAgent.commands_retriever = commands_retriever_chain.retriever

        general_retriever_chain = HybridRetrieverChain(
            embeddings_model_name=embeddings_model_name,
            reranking_model_name=reranking_model_name,
            use_cuda=use_cuda,
            docs_path=[
                './data/markdown/ORFS_docs',
                './data/markdown/OR_docs',
            ],
            manpages_path=['./data/markdown/manpages'],
            contextual_rerank=True,
            search_k=10,
        )
        general_retriever_chain.create_hybrid_retriever()
        RetrieverAgent.general_retriever = general_retriever_chain.retriever

    @staticmethod
    @tool
    def retrieve_general(query: str) -> Tuple[str, list[str]]:
        """
        Retrieve comprehensive and detailed information pertaining to the OpenROAD project and OpenROAD-Flow-Scripts. \
        This includes, but is not limited to, general information, specific functionalities, usage guidelines, \
        troubleshooting steps, and best practices. The tool is designed to assist users by providing clear, accurate, \
        and relevant information that enhances their understanding and efficient use of OpenROAD and OpenROAD-Flow-Scripts.
        """
        if RetrieverAgent.general_retriever is not None:
            docs = RetrieverAgent.general_retriever.invoke(input=query)

        doc_text = ''
        doc_srcs = []
        for doc in docs:
            doc_text += f'\n\n- - - - - - - - - - - - - - - \n\n{doc.page_content}'
            if 'url' in doc.metadata:
                doc_srcs.append(doc.metadata['url'])
            elif 'source' in doc.metadata:
                doc_srcs.append(doc.metadata['source'])

        return doc_text, doc_srcs

    @staticmethod
    @tool
    def retrieve_cmds(query: str) -> Tuple[str, list[str]]:
        """
        The Command Retriever Tool is designed to provide detailed and comprehensive information on the commands and tools available in the OpenROAD project and OpenROAD-Flow-Scripts. This includes descriptions, usage guidelines, command syntax, examples, and best practices. The tool assists users by delivering clear, accurate, and relevant details to help them effectively utilize the following commands and tools within OpenROAD and OpenROAD-Flow-Scripts:

            Antenna Rule Checker
            Clock Tree Synthesis
            Design For Testing
            Detailed Placement
            Detailed Routing
            Metal Fill
            Floorplanning
            Global Placement
            Global Routing
            Graphical User Interface
            Initialize Floorplan
            Macro Placement
            Hierarchical Macro Placement
            OpenDB
            Chip-level Connections
            Pad
            Partition Manager
            Power Distribution Network
            Pin Placement
            IR Drop Analysis
            Parasitics Extraction
            Restructure
            Gate Resizer
            Rectilinear Steiner Tree
            TapCell
            Read Unified Power Format
            Utilities

        This tool aims to be an essential resource for users, providing all necessary information to maximize their productivity and efficiency when working with OpenROAD and OpenROAD-Flow-Scripts.
        """
        if RetrieverAgent.commands_retriever is not None:
            docs = RetrieverAgent.commands_retriever.invoke(input=query)

        doc_text = ''
        doc_srcs = []
        for doc in docs:
            doc_text += f'\n\n- - - - - - - - - - - - - - - \n\n{doc.page_content}'
            if 'url' in doc.metadata:
                doc_srcs.append(doc.metadata['url'])
            elif 'source' in doc.metadata:
                doc_srcs.append(doc.metadata['source'])

        return doc_text, doc_srcs

    @staticmethod
    @tool
    def retrieve_install(query: str) -> Tuple[str, list[str]]:
        """
        Retrieve comprehensive and detailed information pertaining to the installaion of OpenROAD project and OpenROAD-Flow-Scripts. \
        This includes, but is not limited to, various dependencies, system requirements, installation methods such as,
        - Building from source
        - Using Docker
        - Using pre-built binaries
    
        The tool is designed to assist users by providing clear, accurate, and relevant information that enhances their understanding and efficient use of OpenROAD and OpenROAD-Flow-Scripts.
        """
        if RetrieverAgent.install_retriever is not None:
            docs = RetrieverAgent.install_retriever.invoke(input=query)

        doc_text = ''
        doc_srcs = []
        for doc in docs:
            doc_text += f'\n\n- - - - - - - - - - - - - - - \n\n{doc.page_content}'
            if 'url' in doc.metadata:
                doc_srcs.append(doc.metadata['url'])
            elif 'source' in doc.metadata:
                doc_srcs.append(doc.metadata['source'])

        return doc_text, doc_srcs

    @staticmethod
    @tool
    def retrieve_opensta(query: str) -> Tuple[str, list[str]]:
        """
        The OpenSTA Information Retriever tool is designed to provide detailed and comprehensive information about OpenSTA and its various commands.
        This tool aids users by offering clear, accurate, and relevant details, helping them effectively utilize OpenSTA for their timing analysis needs. The tool covers the following aspects:

        Command Line Arguments: Detailed information about the different command line arguments that can be used with OpenSTA.
        Example Command Scripts: Examples of command scripts for different scenarios, including reading designs, performing timing analysis, and power analysis.
        Timing Analysis using SDF: Instructions and examples for performing timing analysis using Standard Delay Format (SDF).
        Timing Analysis with Multiple Process Corners: Guidelines and examples for conducting timing analysis across multiple process corners.
        Power Analysis: Steps and commands involved in performing power analysis.
        TCL Interpreter: Details on using the TCL interpreter with OpenSTA.
        Commands: Comprehensive list and descriptions of all commands available in OpenSTA, along with usage guidelines and examples.
        Filter Expressions: Information on filter expressions used within OpenSTA commands.
        Variables: Descriptions of various variables used in OpenSTA and their purposes.

        This tool aims to be an indispensable resource for users seeking to maximize the utility of OpenSTA by providing easy access to its extensive command set and functionalities.
        """
        if RetrieverAgent.opensta_retriever is not None:
            docs = RetrieverAgent.opensta_retriever.invoke(input=query)

        doc_text = ''
        doc_srcs = []
        for doc in docs:
            doc_text += f'\n\n- - - - - - - - - - - - - - - \n\n{doc.page_content}'
            if 'url' in doc.metadata:
                doc_srcs.append(doc.metadata['url'])
            elif 'source' in doc.metadata:
                doc_srcs.append(doc.metadata['source'])

        return doc_text, doc_srcs
