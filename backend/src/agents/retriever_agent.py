from ..chains.hybrid_retriever_chain import HybridRetrieverChain

from langchain_core.tools import tool
from langchain.retrievers import EnsembleRetriever
from langchain.retrievers import ContextualCompressionRetriever

from ..tools.format_docs import format_docs

import os
from typing import Tuple, Optional, Union
from dotenv import load_dotenv

load_dotenv()

search_k = int(os.getenv('SEARCH_K', 10))
chunk_size = int(os.getenv('CHUNK_SIZE', 4000))


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
            html_docs_path=['./data/rtdocs/yosyshq.readthedocs.io/'],
            weights=[0.6, 0.2, 0.2],
            contextual_rerank=True,
            search_k=search_k,
            chunk_size=chunk_size,
        )
        yosys_rtdocs_retriever_chain.create_hybrid_retriever()
        RetrieverAgent.yosys_rtdocs_retriever = yosys_rtdocs_retriever_chain.retriever

        install_retriever_chain = HybridRetrieverChain(
            embeddings_config=embeddings_config,
            reranking_model_name=reranking_model_name,
            use_cuda=use_cuda,
            markdown_docs_path=[
                './data/markdown/ORFS_docs/installation',
                './data/markdown/OR_docs/installation',
                './data/markdown/gh_discussions/Build',
                './data/markdown/gh_discussions/Installation',
            ],
            weights=[0.6, 0.2, 0.2],
            contextual_rerank=True,
            search_k=search_k,
            chunk_size=chunk_size,
        )
        install_retriever_chain.create_hybrid_retriever()
        RetrieverAgent.install_retriever = install_retriever_chain.retriever

        commands_retriever_chain = HybridRetrieverChain(
            embeddings_config=embeddings_config,
            reranking_model_name=reranking_model_name,
            use_cuda=use_cuda,
            markdown_docs_path=['./data/markdown/OR_docs/tools'],
            manpages_path=[
                './data/markdown/manpages/man1',
                './data/markdown/manpages/man2',
                './data/markdown/gh_discussions/Query',
                './data/markdown/gh_discussions/Runtime',
                './data/markdown/gh_discussions/Documentation',
            ],
            weights=[0.6, 0.2, 0.2],
            contextual_rerank=True,
            search_k=search_k,
            chunk_size=chunk_size,
        )
        commands_retriever_chain.create_hybrid_retriever()
        RetrieverAgent.commands_retriever = commands_retriever_chain.retriever

        opensta_retriever_chain = HybridRetrieverChain(
            embeddings_config=embeddings_config,
            reranking_model_name=reranking_model_name,
            use_cuda=use_cuda,
            other_docs_path=['./data/pdf/OpenSTA/OpenSTA_docs.pdf'],
            weights=[0.6, 0.2, 0.2],
            contextual_rerank=True,
            search_k=search_k,
            chunk_size=chunk_size,
        )
        opensta_retriever_chain.create_hybrid_retriever()
        RetrieverAgent.opensta_retriever = opensta_retriever_chain.retriever

        general_retriever_chain = HybridRetrieverChain(
            embeddings_config=embeddings_config,
            reranking_model_name=reranking_model_name,
            use_cuda=use_cuda,
            markdown_docs_path=[
                './data/markdown/ORFS_docs',
                './data/markdown/OR_docs',
                './data/markdown/gh_discussions',
            ],
            manpages_path=[
                './data/markdown/manpages/man1',
                './data/markdown/manpages/man2',
            ],
            weights=[0.6, 0.2, 0.2],
            contextual_rerank=True,
            search_k=search_k,
            chunk_size=chunk_size,
        )
        general_retriever_chain.create_hybrid_retriever()
        RetrieverAgent.general_retriever = general_retriever_chain.retriever

        errinfo_retriever_chain = HybridRetrieverChain(
            embeddings_config=embeddings_config,
            reranking_model_name=reranking_model_name,
            use_cuda=use_cuda,
            markdown_docs_path=[
                './data/markdown/manpages/man3',
                './data/markdown/gh_discussions/Bug',
            ],
            weights=[0.6, 0.2, 0.2],
            contextual_rerank=True,
            search_k=search_k,
            chunk_size=chunk_size,
        )
        errinfo_retriever_chain.create_hybrid_retriever()
        RetrieverAgent.errinfo_retriever = errinfo_retriever_chain.retriever

    @staticmethod
    @tool
    def retrieve_general(query: str) -> Tuple[str, list[str], list[str]]:
        """
        Retrieve comprehensive and detailed information pertaining to the OpenROAD project and OpenROAD-Flow-Scripts. \
        This includes, but is not limited to, general information, specific functionalities, usage guidelines, \
        troubleshooting steps, and best practices. The tool is designed to assist users by providing clear, accurate, \
        and relevant information that enhances their understanding and efficient use of OpenROAD and OpenROAD-Flow-Scripts.
        """
        if RetrieverAgent.general_retriever is None:
            raise ValueError('General Retriever not initialized')

        docs = RetrieverAgent.general_retriever.invoke(input=query)
        return format_docs(docs)

    @staticmethod
    @tool
    def retrieve_cmds(query: str) -> Tuple[str, list[str], list[str]]:
        """
        Retrieve information on the commands and tools available in the OpenROAD project and OpenROAD-Flow-Scripts. \
        This includes descriptions, usage guidelines, command syntax, examples, and best practices.
        The tool assists users by delivering clear, accurate, and relevant details to help them effectively utilize the following commands and tools within OpenROAD and OpenROAD-Flow-Scripts:
 
        Here's a list of all the tools available:
        ANT: Antenna Rule Checker
        CTS: Clock Tree Synthesis
        DFT: Design For Testing
        DPL: Detailed Placement
        DRT: Detailed Routing
        FIN: Metal Fill
        GPL: Global Floorplanning
        GPL: Global Placement
        GRT: Global Routing
        GUI: Graphical User Interface
        IFP: Initialize Floorplan
        MPL: Macro Placement
        MPL: Hierarchical Macro Placement
        ODB: OpenDB
        Chip-level Connections
        PAD: Pad
        PAR: Partition Manager
        PDN: Power Distribution Network
        PPL: Pin Placement
        PSM: IR Drop Analysis
        RSX: Parasitics Extraction
        RMP: Restructure
        RSZ: Gate Resizer
        STT: Rectilinear Steiner Tree
        TAP: TapCell
        UPF: Read Unified Power Format
        UTL: Utilities

        The tools can be represented by their abbreviations as well: ANT,CTS,DFT,DPL,DRT,FIN,GPL,GRT,GUI,IFP,MPL,ODB,PAD,PAR,PDN,PPL,PSM,RSX,RMP,RSZ,STT,TAP,UPF,UTL     
        
        """
        if RetrieverAgent.commands_retriever is None:
            raise ValueError('Commands Retriever not initialized')

        docs = RetrieverAgent.commands_retriever.invoke(input=query)
        return format_docs(docs)

    @staticmethod
    @tool
    def retrieve_install(query: str) -> Tuple[str, list[str], list[str]]:
        """
        Retrieve comprehensive and detailed information pertaining to the installaion of OpenROAD project and OpenROAD-Flow-Scripts. \
        This includes, but is not limited to, various dependencies, system requirements, installation methods such as,
        - Building from source
        - Using Docker
        - Using pre-built binaries
    
        This tool is designed to assist users by providing clear, accurate, and relevant information that enhances their understanding and efficient use of OpenROAD and OpenROAD-Flow-Scripts.
        """
        if RetrieverAgent.install_retriever is None:
            raise ValueError('Install Retriever not initialized')

        docs = RetrieverAgent.install_retriever.invoke(input=query)
        return format_docs(docs)

    @staticmethod
    @tool
    def retrieve_opensta(query: str) -> Tuple[str, list[str], list[str]]:
        """
        Retrieve detailed and comprehensive information about OpenSTA and its various commands.
        
        OpenSTA is an open-source gate-level static timing verifier that has been used by many design houses.\
        As a stand-alone executable it can be used to verify the timing of a design using standard file formats.

        Verilog netlist
        Liberty library
        SDC timing constraints
        SDF delay annotation
        SPEF parasitics

        Command Line Arguments: Detailed information about the different command line arguments that can be used with OpenSTA.
        Example Command Scripts: Examples of command scripts for different scenarios, including reading designs, performing timing analysis, and power analysis.
        Timing Analysis using SDF: Instructions and examples for performing timing analysis using Standard Delay Format (SDF).
        Timing Analysis with Multiple Process Corners: Guidelines and examples for conducting timing analysis across multiple process corners.
        Power Analysis: Steps and commands involved in performing power analysis.
        TCL Interpreter: Details on using the TCL interpreter with OpenSTA.
        Commands: Comprehensive list and descriptions of all commands available in OpenSTA, along with usage guidelines and examples.
        Filter Expressions: Information on filter expressions used within OpenSTA commands.
        Variables: Descriptions of various variables used in OpenSTA and their purposes.

        """
        if RetrieverAgent.opensta_retriever is None:
            raise ValueError('OpenSTA Retriever not initialized')

        docs = RetrieverAgent.opensta_retriever.invoke(input=query)
        return format_docs(docs)

    @staticmethod
    @tool
    def retrieve_errinfo(query: str) -> Tuple[str, list[str], list[str]]:
        """
        Retrieve descriptions and details regarding the various warning/error messages encountered while using the OpenROAD.
        An error code usually is identified by the tool, followed by a number.
        Examples: ANT-0001, CTS-0014 etc.
        """

        if RetrieverAgent.errinfo_retriever is None:
            raise ValueError('Error Info Retriever not initialized')

        docs = RetrieverAgent.errinfo_retriever.invoke(input=query)
        return format_docs(docs)

    @staticmethod
    @tool
    def retrieve_yosys_rtdocs(query: str) -> Tuple[str, list[str], list[str]]:
        """
        Retrieve detailed information regarding the Yosys application. \
        This tool provides comprehensive information on the various functionalities, commands, and usage guidelines of Yosys.\
        This tool provides information pertaining to the installation, usage, and troubleshooting of Yosys.\
        
        Yosys is a framework for Verilog RTL synthesis. \
        It currently has extensive Verilog-2005 support and provides a basic set of synthesis algorithms for various application domains. \
        """

        if RetrieverAgent.yosys_rtdocs_retriever is None:
            raise ValueError('Yosys RTDocs Retriever not initialized')

        docs = RetrieverAgent.yosys_rtdocs_retriever.invoke(input=query)
        return format_docs(docs)
