from fastmcp import FastMCP


class ORFS():
    mcp = FastMCP("ORFS")
    server = None

    llm = None
    general_retriever = None
    install_retriever = None
    commands_retriever = None
    yosys_rtdocs_retriever = None
    klayout_retriever = None
    errinfo_retriever = None
