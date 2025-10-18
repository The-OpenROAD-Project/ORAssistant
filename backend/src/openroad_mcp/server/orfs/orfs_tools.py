from typing import Any, Optional
from fastmcp import FastMCP


class ORFS:
    mcp = FastMCP("ORFS")
    server: Optional[Any] = None

    llm: Optional[Any] = None
    general_retriever: Optional[Any] = None
    install_retriever: Optional[Any] = None
    commands_retriever: Optional[Any] = None
    yosys_rtdocs_retriever: Optional[Any] = None
    klayout_retriever: Optional[Any] = None
    errinfo_retriever: Optional[Any] = None
