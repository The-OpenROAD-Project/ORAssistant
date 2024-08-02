from ..chains.hybrid_retriever_chain import HybridRetrieverChain

from langchain_core.tools import tool
from langchain.retrievers import EnsembleRetriever
from langchain.retrievers import ContextualCompressionRetriever

import os
from typing import Tuple, Optional, Union
from dotenv import load_dotenv

load_dotenv()

search_k = os.getenv('SEARCH_K', 10) 

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
    errinfo_retriever: Optional[
        Union[EnsembleRetriever, ContextualCompressionRetriever]
    ]
    yosys_rtdocs_retriever: Optional[
        Union[EnsembleRetriever, ContextualCompressionRetriever]
    ]

    def initialize(
        self,
        embeddings_config: dict[str, str],
        reranking_model_name: str,
        use_cuda: bool = False,
    ) -> None:
        yosys_rtdocs_retriever_chain = HybridRetrieverChain(
            embeddings_config=embeddings_config,
            reranking_model_name=reranking_model_name,
            use_cuda=use_cuda,
            rtdocs_path=[
                '/home/palaniappan-r/Code/ORAssistant/backend/data/rtdocs/yosyshq.readthedocs.io/'
            ],
            contextual_rerank=True,
            search_k=10,
        )
        yosys_rtdocs_retriever_chain.create_hybrid_retriever()
        RetrieverAgent.yosys_rtdocs_retriever = yosys_rtdocs_retriever_chain.retriever

        opensta_retriever_chain = HybridRetrieverChain(
            embeddings_config=embeddings_config,
            reranking_model_name=reranking_model_name,
            use_cuda=use_cuda,
            other_docs_path=['./data/pdf/OpenSTA/OpenSTA_docs.pdf'],
            contextual_rerank=True,
            search_k=10,
        )
        opensta_retriever_chain.create_hybrid_retriever()
        RetrieverAgent.opensta_retriever = opensta_retriever_chain.retriever

        install_retriever_chain = HybridRetrieverChain(
            embeddings_config=embeddings_config,
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
            embeddings_config=embeddings_config,
            reranking_model_name=reranking_model_name,
            use_cuda=use_cuda,
            docs_path=['./data/markdown/OR_docs/tools'],
            manpages_path=[
                './data/markdown/manpages/man1',
                './data/markdown/manpages/man2',
            ],
            contextual_rerank=True,
            search_k=10,
        )
        commands_retriever_chain.create_hybrid_retriever()
        RetrieverAgent.commands_retriever = commands_retriever_chain.retriever

        general_retriever_chain = HybridRetrieverChain(
            embeddings_config=embeddings_config,
            reranking_model_name=reranking_model_name,
            use_cuda=use_cuda,
            docs_path=[
                './data/markdown/ORFS_docs',
                './data/markdown/OR_docs',
            ],
            manpages_path=[
                './data/markdown/manpages/man1',
                './data/markdown/manpages/man2',
            ],
            contextual_rerank=True,
            search_k=10,
        )
        general_retriever_chain.create_hybrid_retriever()
        RetrieverAgent.general_retriever = general_retriever_chain.retriever

        errinfo_retriever_chain = HybridRetrieverChain(
            embeddings_config=embeddings_config,
            reranking_model_name=reranking_model_name,
            use_cuda=use_cuda,
            docs_path=['./data/markdown/manpages/man3'],
            contextual_rerank=True,
            search_k=10,
        )
        errinfo_retriever_chain.create_hybrid_retriever()
        RetrieverAgent.errinfo_retriever = errinfo_retriever_chain.retriever

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
        The Command Retriever Tool is designed to provide detailed and comprehensive information on the commands and tools available in the OpenROAD project and OpenROAD-Flow-Scripts. This includes descriptions, usage guidelines, command syntax, examples, and best practices.
        The tool assists users by delivering clear, accurate, and relevant details to help them effectively utilize the following commands and tools within OpenROAD and OpenROAD-Flow-Scripts:

            Antenna Rule Checker (ANT)
            Clock Tree Synthesis (CTS)
            Design For Testing (DFT)
            Detailed Placement (DPL)
            Detailed Routing (DRT)
            Metal Fill (FIN)
            Global Floorplanning
            Global Placement (GPL)
            Global Routing (GRT)
            Graphical User Interface (GUI)
            Initialize Floorplan (IFP)
            Macro Placement (MPL)
            Hierarchical Macro Placement (MPL)
            OpenDB (ODB)
            Chip-level Connections
            Pad (PAD)
            Partition Manager (PAR)
            Power Distribution Network (PDN)
            Pin Placement (PPL)
            IR Drop Analysis (PSM)
            Parasitics Extraction (RSX)
            Restructure (RMP)
            Gate Resizer (RSZ)
            Rectilinear Steiner Tree (STT)
            TapCell (TAP)
            Read Unified Power Format (UPF)
            Utilities (UTL)

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

    @staticmethod
    @tool
    def retrieve_errinfo(query: str) -> Tuple[str, list[str]]:
        """
        Retrieve descriptions and details regarding the various warning/error messages encountered while using the OpenROAD.
        An error code usually is identified by the tool, followed by a number.
        Examples: ANT-0001, CTS-0014 etc.
        """

        if RetrieverAgent.errinfo_retriever is not None:
            docs = RetrieverAgent.errinfo_retriever.invoke(input=query)

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
    def retrieve_yosys_rtdocs(query: str) -> Tuple[str, list[str]]:
        """
        Retrieve detailed information regarding the Yosys application. \
        This tool provides comprehensive information on the various functionalities, commands, and usage guidelines of Yosys.\
        This tool provides information pertaining to the installation, usage, and troubleshooting of Yosys.\
        """

        if RetrieverAgent.yosys_rtdocs_retriever is not None:
            docs = RetrieverAgent.yosys_rtdocs_retriever.invoke(input=query)

        doc_text = ''
        doc_srcs = []
        for doc in docs:
            doc_text += f'\n\n- - - - - - - - - - - - - - - \n\n{doc.page_content}'
            if 'url' in doc.metadata:
                doc_srcs.append(doc.metadata['url'])
            elif 'source' in doc.metadata:
                doc_srcs.append(doc.metadata['source'])

        return doc_text, doc_srcs
