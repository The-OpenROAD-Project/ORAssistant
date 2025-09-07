from langchain_core.tools import tool


@tool
def arch_info(query: str) -> str:
    """
    Generate OpenROAD infrastructure files and configuration templates.

    Use this tool when the user requests to:
    - Generate or create configuration files (Makefiles, .env files, config templates)
    - Provide environment variable setups or export commands
    - Create project structure templates or boilerplate code
    - Generate Docker/container configuration files
    - Produce setup scripts or installation configurations
    - Create workflow or pipeline configuration files
    - Generate architecture-specific settings or parameter files

    Trigger keywords: generate, create, provide, template, setup, configure, export, scaffold
    Focus: File generation and infrastructure setup rather than information queries or command execution.
    """
    return "mcp_agent"


@tool
def mcp_info(query: str) -> str:
    """
    Execute OpenROAD Flow Scripts (ORFS) commands and system operations.

    Use this tool when the user requests to:
    - Run, execute, or invoke specific ORFS commands (synthesis, floorplan, placement, routing)
    - Perform build operations (make commands, compilation)
    - Execute shell/terminal commands related to OpenROAD workflow
    - Start, launch, or trigger design flow steps
    - Check system status, environment variables, or tool versions
    - Manipulate files or directories in the design environment
    - Configure or initialize OpenROAD projects

    Trigger keywords: run, execute, perform, start, launch, build, compile, make, configure, initialize, check, set
    Action verbs indicating command execution rather than information queries.
    """
    return "mcp_agent"


@tool
def rag_info(query: str) -> str:
    """
    Retrieve information from OpenROAD documentation and knowledge base.

    Use this tool when the user requests to:
    - Find specific information about OpenROAD tools, features, or concepts
    - Look up documentation, tutorials, or installation guides
    - Get explanations of error messages or troubleshooting steps
    - Understand workflow steps, design flows, or methodologies
    - Learn about OpenROAD-flow-scripts (ORFS) usage and configuration
    - Find information about OpenSTA, Yosys, or Klayout integration
    - Get answers to general "what is", "how does", "why" questions
    - Seek onboarding information for new users

    Trigger keywords: what, how, why, explain, find, look up, understand, learn, show, tell me
    Question patterns: Typically phrased as questions rather than commands or requests for file generation.
    Focus: Information retrieval and knowledge sharing rather than execution or file creation.
    """
    return "rag_agent"
