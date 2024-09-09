import os
from typing import Tuple, Optional, Union
from dotenv import load_dotenv

from langchain_core.tools import tool
from langchain.retrievers import EnsembleRetriever
from langchain.retrievers import ContextualCompressionRetriever

from ..chains.hybrid_retriever_chain import HybridRetrieverChain
from ..tools.format_docs import format_docs

load_dotenv()

search_k = int(os.getenv('SEARCH_K', 10))
chunk_size = int(os.getenv('CHUNK_SIZE', 4000))


class RetrieverTools:
    def __init__(self) -> None:
        pass

    install_retriever: Optional[
        Union[EnsembleRetriever, ContextualCompressionRetriever]
    ]
    general_retriever: Optional[
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
    klayout_retriever: Optional[
        Union[EnsembleRetriever, ContextualCompressionRetriever]
    ]
    tool_descriptions: str = ''

    def initialize(
        self,
        embeddings_config: dict[str, str],
        reranking_model_name: str,
        use_cuda: bool = False,
    ) -> None:
        general_retriever_chain = HybridRetrieverChain(
            embeddings_config=embeddings_config,
            reranking_model_name=reranking_model_name,
            use_cuda=use_cuda,
            html_docs_path=['./data/html/or_website/'],
            markdown_docs_path=[
                './data/markdown/OR_docs',
                './data/markdown/ORFS_docs',
                './data/markdown/gh_discussions',
                './data/markdown/manpages/man1',
                './data/markdown/manpages/man2',
            ],
            other_docs_path=['./data/pdf/OR_publications'],
            weights=[0.6, 0.2, 0.2],
            contextual_rerank=True,
            search_k=search_k,
            chunk_size=chunk_size,
        )
        general_retriever_chain.create_hybrid_retriever()
        RetrieverTools.general_retriever = general_retriever_chain.retriever

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
        RetrieverTools.install_retriever = install_retriever_chain.retriever

        commands_retriever_chain = HybridRetrieverChain(
            embeddings_config=embeddings_config,
            reranking_model_name=reranking_model_name,
            use_cuda=use_cuda,
            markdown_docs_path=[
                './data/markdown/OR_docs/tools',
                './data/markdown/ORFS_docs/general',
                './data/markdown/gh_discussions/Query',
                './data/markdown/gh_discussions/Runtime',
                './data/markdown/gh_discussions/Documentation',
                './data/markdown/manpages/man1',
                './data/markdown/manpages/man2',
                './data/markdown/OpenSTA_docs',
            ],
            other_docs_path=['./data/pdf'],
            weights=[0.6, 0.2, 0.2],
            contextual_rerank=True,
            search_k=search_k,
            chunk_size=chunk_size,
        )
        commands_retriever_chain.create_hybrid_retriever()
        RetrieverTools.commands_retriever = commands_retriever_chain.retriever

        yosys_rtdocs_retriever_chain = HybridRetrieverChain(
            embeddings_config=embeddings_config,
            reranking_model_name=reranking_model_name,
            use_cuda=use_cuda,
            html_docs_path=['./data/html/yosys_docs'],
            weights=[0.6, 0.2, 0.2],
            contextual_rerank=True,
            search_k=search_k,
            chunk_size=chunk_size,
        )
        yosys_rtdocs_retriever_chain.create_hybrid_retriever()
        RetrieverTools.yosys_rtdocs_retriever = yosys_rtdocs_retriever_chain.retriever

        klayout_retriever_chain = HybridRetrieverChain(
            embeddings_config=embeddings_config,
            reranking_model_name=reranking_model_name,
            use_cuda=use_cuda,
            html_docs_path=['./data/html/klayout_docs'],
            weights=[0.6, 0.2, 0.2],
            contextual_rerank=True,
            search_k=search_k,
            chunk_size=chunk_size,
        )
        klayout_retriever_chain.create_hybrid_retriever()
        RetrieverTools.klayout_retriever = klayout_retriever_chain.retriever

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
        RetrieverTools.errinfo_retriever = errinfo_retriever_chain.retriever

    @staticmethod
    @tool
    def retrieve_general(query: str) -> Tuple[str, list[str], list[str]]:
        """
        Retrieve comprehensive and detailed information pertaining to the OpenROAD project and OpenROAD-Flow-Scripts.\
        This includes, but is not limited to, general information, specific functionalities, usage guidelines,\
        troubleshooting steps, and best practices. The tool is designed to assist users by providing clear, accurate,\
        and relevant information that enhances their understanding and efficient use of OpenROAD and OpenROAD-Flow-Scripts.\
        """
        if RetrieverTools.general_retriever is None:
            raise ValueError('General Retriever not initialized')

        docs = RetrieverTools.general_retriever.invoke(input=query)
        return format_docs(docs)

    @staticmethod
    @tool
    def retrieve_cmds(query: str) -> Tuple[str, list[str], list[str]]:
        """
        Retrieve information on the commands available in OpenROAD, OpenROAD-Flow-Scripts and OpenSTA.\
        This includes usage guidelines, command syntax, examples, and best practices about commands that cover various \
        aspects of electronic design automation, such as synthesis, placement, routing, analysis, and \
        optimization within the OpenROAD environment.

        OR and ORFS Commands:
        Antenna Rule Checker (ANT), Clock Tree Synthesis (CTS), Design For Testing (DFT), Detailed Placement (DPL), \
        Detailed Routing (DRT), Metal Fill (FIN), Floorplanning, Global Placement (GPL), Global Routing (GRT), Graphical User Interface (GUI), \
        Initialize Floorplan (IFP), Macro Placement (MPL), Hierarchical Macro Placement (MPL2), OpenDB (ODB), Chip-level Connections (PAD),\
        Partition Manager (PAR), Power Distribution Network (PDN), Pin Placement (PPL), IR Drop Analysis (PSM), Parasitics Extraction (RSX),\
        Restructure (RMP), Gate Resizer (RSZ), Rectilinear Steiner Tree (STT), TapCell (TAP), Read Unified Power Format (UPF), Timing Optimization\
       
        OpenSTA is an open-source gate-level static timing verifier.\
        It can verify the timing of deisgns in the form of Verilog netlists.\
        Timing Analysis: Perform static timing analysis using standard file formats (Verilog, Liberty, SDC, SDF, SPEF).
        Multiple Process Corners: Conduct analysis across different process variations.
        Power Analysis: Evaluate power consumption in designs.
        TCL Interpreter: Use TCL scripts for command automation and customization.
        """
        if RetrieverTools.commands_retriever is None:
            raise ValueError('Commands Retriever not initialized')

        docs = RetrieverTools.commands_retriever.invoke(input=query)
        return format_docs(docs)

    @staticmethod
    @tool
    def retrieve_install(query: str) -> Tuple[str, list[str], list[str]]:
        """
        Retrieve comprehensive and detailed information pertaining to the installaion of OpenROAD project and OpenROAD-Flow-Scripts.\
        This includes, but is not limited to, various dependencies, system requirements, installation methods such as,\
        - Building from source\
        - Using Docker\
        - Using pre-built binaries\
        """
        if RetrieverTools.install_retriever is None:
            raise ValueError('Install Retriever not initialized')

        docs = RetrieverTools.install_retriever.invoke(input=query)
        return format_docs(docs)

    @staticmethod
    @tool
    def retrieve_errinfo(query: str) -> Tuple[str, list[str], list[str]]:
        """
        Retrieve descriptions and details regarding the various warning/error messages encountered while using the OpenROAD.\
        An error code usually is identified by the tool, followed by a number.\
        Examples: ANT-0001, CTS-0014 etc.\
        """

        if RetrieverTools.errinfo_retriever is None:
            raise ValueError('Error Info Retriever not initialized')

        docs = RetrieverTools.errinfo_retriever.invoke(input=query)
        return format_docs(docs)

    @staticmethod
    @tool
    def retrieve_yosys_rtdocs(query: str) -> Tuple[str, list[str], list[str]]:
        """
        Retrieve detailed information regarding the Yosys application.\
        This tool provides information pertaining to the installation, usage, and troubleshooting of Yosys.\
        
        Yosys is a framework for Verilog RTL synthesis.\
        It currently has extensive Verilog-2005 support and provides a basic set of synthesis algorithms for various application domains.\
        Setup: Configure Yosys for synthesis tasks.
        Usage: Execute synthesis commands and scripts.
        Troubleshooting: Resolve common issues in synthesis flows.
        """

        if RetrieverTools.yosys_rtdocs_retriever is None:
            raise ValueError('Yosys RTDocs Retriever not initialized')

        docs = RetrieverTools.yosys_rtdocs_retriever.invoke(input=query)
        return format_docs(docs)

    @staticmethod
    @tool
    def retrieve_klayout_docs(query: str) -> Tuple[str, list[str], list[str]]:
        """
        Retrieve detailed information regarding the KLayout application.\
        This tool provides information pertaining to the installation, usage, and troubleshooting of KLayout.\
        
        KLayout is a powerful open-source layout viewer and editor designed for integrated circuit (IC) design.\
        It supports various file formats, including GDSII, OASIS, and DXF
        """

        if RetrieverTools.klayout_retriever is None:
            raise ValueError('KLayout Retriever not initialized')

        docs = RetrieverTools.klayout_retriever.invoke(input=query)
        return format_docs(docs)
