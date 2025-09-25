import os
import logging
from orfs_tools import ORFS

from typing import Tuple
from langchain_ollama import ChatOllama
from chains.hybrid_retriever_chain import HybridRetrieverChain
from chains.tools.format_docs import format_docs

class ORFSRag(ORFS):
    required_env_vars = [
        "USE_CUDA",
        "LLM_TEMP",
        "HF_EMBEDDINGS",
        "HF_RERANKER",
        "LLM_MODEL",
    ]
    hf_reranker: str = str(os.getenv("HF_RERANKER"))
    reranking_model_name=hf_reranker
    embeddings_type: str = str(os.getenv("EMBEDDINGS_TYPE"))
    use_cuda: bool = False
    if str(os.getenv("USE_CUDA")).lower() in ("true"):
        use_cuda = True

    if embeddings_type == "HF":
        embeddings_model_name = str(os.getenv("HF_EMBEDDINGS"))
    elif embeddings_type == "GOOGLE_GENAI" or embeddings_type == "GOOGLE_VERTEXAI":
        embeddings_model_name = str(os.getenv("GOOGLE_EMBEDDINGS"))
    else:
        raise ValueError(
            "EMBEDDINGS_TYPE environment variable must be set to 'HF', 'GOOGLE_GENAI', or 'GOOGLE_VERTEXAI'."
        )

    embeddings_config = {"type": embeddings_type, "name": embeddings_model_name}
    fast_mode: bool = False
    markdown_docs_map = {
        "general": [
            "./data/markdown/OR_docs",
            "./data/markdown/ORFS_docs",
            "./data/markdown/gh_discussions",
            "./data/markdown/manpages/man1",
            "./data/markdown/manpages/man2",
            "./data/markdown/OpenSTA_docs",
        ],
        "install": [
            "./data/markdown/ORFS_docs/installation",
            "./data/markdown/OR_docs/installation",
            "./data/markdown/gh_discussions/Build",
            "./data/markdown/gh_discussions/Installation",
            "./data/markdown/OpenSTA_docs",
        ],
        "commands": [
            "./data/markdown/OR_docs/tools",
            "./data/markdown/ORFS_docs/general",
            "./data/markdown/gh_discussions/Query",
            "./data/markdown/gh_discussions/Runtime",
            "./data/markdown/gh_discussions/Documentation",
            "./data/markdown/manpages/man1",
            "./data/markdown/manpages/man2",
            "./data/markdown/OpenSTA_docs",
        ],
        "errinfo": [
            "./data/markdown/manpages/man3",
            "./data/markdown/gh_discussions/Bug",
        ],
    }
    search_k = int(os.getenv("SEARCH_K", 10))
    chunk_size = int(os.getenv("CHUNK_SIZE", 4000))
    #llm: ChatGoogleGenerativeAI | ChatVertexAI | ChatOllama

    llm_temp_str = os.getenv("LLM_TEMP")
    if llm_temp_str is not None:
        llm_temp = float(llm_temp_str)

    if os.getenv("LLM_MODEL") == "ollama":
        model_name = str(os.getenv("OLLAMA_MODEL"))
        ORFS.llm = ChatOllama(model=model_name, temperature=llm_temp)
        logging.info(ORFS.llm)
    # TODO: try with gemini
    #elif os.getenv("LLM_MODEL") == "gemini":
    #    if os.getenv("GOOGLE_GEMINI") == "1_pro":
    #        llm = ChatGoogleGenerativeAI(model="gemini-pro", temperature=llm_temp)
    #    elif os.getenv("GOOGLE_GEMINI") == "1.5_flash":
    #        llm = ChatVertexAI(model_name="gemini-1.5-flash", temperature=llm_temp)
    #    elif os.getenv("GOOGLE_GEMINI") == "1.5_pro":
    #        llm = ChatVertexAI(model_name="gemini-1.5-pro", temperature=llm_temp)
    #    else:
    #        raise ValueError("GOOGLE_GEMINI environment variable not set to a valid value.")
    #
    else:
        raise ValueError("LLM_MODEL environment variable not set to a valid value.")
    ###
    # TODO: remove fast_mode or keep?
    general_retriever_chain = HybridRetrieverChain(
        embeddings_config=embeddings_config,
        reranking_model_name=reranking_model_name,
        use_cuda=use_cuda,
        #html_docs_path=[] if fast_mode else ["./data/html/or_website/"],
        #markdown_docs_path=fastmode_docs_map["general"]
        #if fast_mode
        #else markdown_docs_map["general"],
        #other_docs_path=[] if fast_mode else ["./data/pdf"],
        html_docs_path=["./data/html/or_website/"],
        markdown_docs_path=markdown_docs_map["general"],
        other_docs_path=["./data/pdf"],
        weights=[0.6, 0.2, 0.2],
        contextual_rerank=True,
        search_k=search_k,
        chunk_size=chunk_size,
    )
    general_retriever_chain.create_hybrid_retriever()
    ORFS.general_retriever = general_retriever_chain.retriever

    install_retriever_chain = HybridRetrieverChain(
        embeddings_config=embeddings_config,
        reranking_model_name=reranking_model_name,
        use_cuda=use_cuda,
        #markdown_docs_path=fastmode_docs_map["install"]
        #if fast_mode
        #else markdown_docs_map["install"],
        markdown_docs_path=markdown_docs_map["install"],
        weights=[0.6, 0.2, 0.2],
        contextual_rerank=True,
        search_k=search_k,
        chunk_size=chunk_size,
    )
    install_retriever_chain.create_hybrid_retriever()
    ORFS.install_retriever = install_retriever_chain.retriever

    commands_retriever_chain = HybridRetrieverChain(
        embeddings_config=embeddings_config,
        reranking_model_name=reranking_model_name,
        use_cuda=use_cuda,
        #markdown_docs_path=fastmode_docs_map["commands"]
        #if fast_mode
        #else markdown_docs_map["commands"],
        #other_docs_path=[] if fast_mode else ["./data/pdf"],
        markdown_docs_path=markdown_docs_map["commands"],
        other_docs_path=["./data/pdf"],
        weights=[0.6, 0.2, 0.2],
        contextual_rerank=True,
        search_k=search_k,
        chunk_size=chunk_size,
    )
    commands_retriever_chain.create_hybrid_retriever()
    ORFS.commands_retriever = commands_retriever_chain.retriever

    yosys_rtdocs_retriever_chain = HybridRetrieverChain(
        embeddings_config=embeddings_config,
        reranking_model_name=reranking_model_name,
        use_cuda=use_cuda,
        #html_docs_path=fastmode_docs_map["yosys"]
        #if fast_mode
        #else ["./data/html/yosys_docs"],
        html_docs_path=["./data/html/yosys_docs"],
        weights=[0.6, 0.2, 0.2],
        contextual_rerank=True,
        search_k=search_k,
        chunk_size=chunk_size,
    )
    yosys_rtdocs_retriever_chain.create_hybrid_retriever()
    ORFS.yosys_rtdocs_retriever = yosys_rtdocs_retriever_chain.retriever

    klayout_retriever_chain = HybridRetrieverChain(
        embeddings_config=embeddings_config,
        reranking_model_name=reranking_model_name,
        use_cuda=use_cuda,
        #html_docs_path=fastmode_docs_map["klayout"]
        #if fast_mode
        #else ["./data/html/klayout_docs"],
        html_docs_path=["./data/html/klayout_docs"],
        weights=[0.6, 0.2, 0.2],
        contextual_rerank=True,
        search_k=search_k,
        chunk_size=chunk_size,
    )
    klayout_retriever_chain.create_hybrid_retriever()
    ORFS.klayout_retriever = klayout_retriever_chain.retriever

    errinfo_retriever_chain = HybridRetrieverChain(
        embeddings_config=embeddings_config,
        reranking_model_name=reranking_model_name,
        use_cuda=use_cuda,
        #markdown_docs_path=fastmode_docs_map["errinfo"]
        #if fast_mode
        #else markdown_docs_map["errinfo"],
        markdown_docs_path=markdown_docs_map["errinfo"],
        weights=[0.6, 0.2, 0.2],
        contextual_rerank=True,
        search_k=search_k,
        chunk_size=chunk_size,
    )
    errinfo_retriever_chain.create_hybrid_retriever()
    ORFS.errinfo_retriever = errinfo_retriever_chain.retriever

    # TODO: make callable as mcp tool?
    @staticmethod
    @ORFS.mcp.tool
    def retrieve_general(self, query: str) -> Tuple[str, list[str], list[str], list[str]]:
        """
        Retrieve comprehensive and detailed information pertaining to the OpenROAD project, OpenROAD-Flow-Scripts and OpenSTA.\
        This includes, but is not limited to, general information, specific functionalities, usage guidelines,\
        troubleshooting steps, and best practices. The tool is designed to assist users by providing clear, accurate,\
        and relevant information that enhances their understanding and efficient use of OpenROAD and OpenROAD-Flow-Scripts.\
        """
        if ORFS.general_retriever is None:
            raise ValueError("General Retriever not initialized")
        else:
            docs = ORFS.general_retriever.invoke(input=query)
            return format_docs(docs)

    @staticmethod
    @ORFS.mcp.tool
    def retrieve_cmds(query: str) -> Tuple[str, list[str], list[str], list[str]]:
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
        Timing Analysis: Perform static timing analysis using standard file formats (Verilog, Liberty, SDC, SDF, SPEF). \
        Multiple Process Corners: Conduct analysis across different process variations. \
        Power Analysis: Evaluate power consumption in designs. \
        TCL Interpreter: Use TCL scripts for command automation  and customization. \
        """
        if ORFS.commands_retriever is None:
            raise ValueError("Commands Retriever not initialized")
        else:
            docs = ORFS.commands_retriever.invoke(input=query)
            return format_docs(docs)

    @staticmethod
    @ORFS.mcp.tool
    def retrieve_install(query: str) -> Tuple[str, list[str], list[str], list[str]]:
        """
        Retrieve comprehensive and detailed information pertaining to the installaion of OpenROAD, OpenROAD-Flow-Scripts and OpenSTA.\
        This includes, but is not limited to, various dependencies, system requirements, installation methods such as,\
        - Building from source\
        - Using Docker\
        - Using pre-built binaries\
        """
        if ORFS.install_retriever is None:
            raise ValueError("Install Retriever not initialized")
        else:
            docs = ORFS.install_retriever.invoke(input=query)
            return format_docs(docs)

    @staticmethod
    @ORFS.mcp.tool
    def retrieve_errinfo(query: str) -> Tuple[str, list[str], list[str], list[str]]:
        """
        Retrieve descriptions and details regarding the various warning/error messages encountered while using the OpenROAD.\
        An error code usually is identified by the tool, followed by a number.\
        Examples: ANT-0001, CTS-0014 etc.\
        """

        if ORFS.errinfo_retriever is None:
            raise ValueError("Error Info Retriever not initialized")
        else:
            docs = ORFS.errinfo_retriever.invoke(input=query)
            return format_docs(docs)

    @staticmethod
    @ORFS.mcp.tool
    def retrieve_yosys_rtdocs(
        query: str,
    ) -> Tuple[str, list[str], list[str], list[str]]:
        """
        Retrieve detailed information regarding the Yosys application.\
        This tool provides information pertaining to the installation, usage, and troubleshooting of Yosys.\

        Yosys is a framework for Verilog RTL synthesis.\
        It currently has extensive Verilog-2005 support and provides a basic set of synthesis algorithms for various application domains.\
        Setup: Configure Yosys for synthesis tasks.
        Usage: Execute synthesis commands and scripts.
        Troubleshooting: Resolve common issues in synthesis flows.
        """

        if ORFS.yosys_rtdocs_retriever is None:
            raise ValueError("Yosys RTDocs Retriever not initialized")
        else:
            docs = retrievertools.yosys_rtdocs_retriever.invoke(input=query)
            return format_docs(docs)

    @staticmethod
    @ORFS.mcp.tool
    def retrieve_klayout_docs(
        query: str,
    ) -> Tuple[str, list[str], list[str], list[str]]:
        """
        Retrieve detailed information regarding the KLayout application.\
        This tool provides information pertaining to the installation, usage, and troubleshooting of KLayout.\

        KLayout is a powerful open-source layout viewer and editor designed for integrated circuit (IC) design.\
        It supports various file formats, including GDSII, OASIS, and DXF
        """

        if ORFS.klayout_retriever is None:
            raise ValueError("KLayout Retriever not initialized")
        else:
            docs = ORFS.klayout_retriever.invoke(input=query)
            return format_docs(docs)
