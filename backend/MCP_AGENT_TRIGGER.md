# MCP Agent Trigger Guide

## Overview
The MCP (Model Context Protocol) agent is triggered when users want to run commands or perform shell/system actions related to OpenROAD infrastructure. It connects to an MCP server running on `http://localhost:3001/mcp/` to execute ORFS (OpenROAD-Flow-Scripts) commands.

## How MCP Agent Gets Triggered

### 1. Query Classification
When a user sends a query, the system first classifies it into one of three categories:
- **rag_info**: Information retrieval from documentation
- **mcp_info**: Command execution or shell actions  
- **arch_info**: Generate OpenROAD infrastructure files

The MCP agent is triggered when the query is classified as `mcp_info`.

### 2. Trigger Keywords and Patterns
The MCP agent is typically triggered by queries that:
- Request to **run** or **execute** commands
- Involve **terminal** or **shell** operations  
- Request **system actions** or **environment changes**
- Include action verbs like: run, execute, perform, start, launch, build, compile

## Example Queries That Trigger MCP Agent

### Command Execution
```
"Run synthesis on my design"
"Execute the floorplan command"
"Start the placement flow"
"Build my RTL design with Yosys"
"Compile the Verilog files"
```

### Shell/Terminal Actions
```
"Show me the ORFS environment variables"
"Check the current OpenROAD version"
"List available ORFS make targets"
"Run make in the design directory"
```

### System Operations
```
"Set up the OpenROAD environment"
"Configure the design parameters"
"Initialize a new ORFS project"
"Clean the build directory"
```

## Example Queries That DON'T Trigger MCP (Go to RAG Instead)

### Information Queries
```
"What is OpenROAD?"
"How does placement work?"
"Explain the synthesis flow"
"What are the available PDKs?"
"Tell me about timing analysis"
```

### Documentation Requests
```
"Show me the documentation for global placement"
"What are the parameters for detailed routing?"
"How to use the timing report commands?"
```

## MCP Server Requirements

For the MCP agent to work:
1. MCP server must be running at `http://localhost:3001`
2. Health check endpoint must be available at `/health`
3. Server must provide ORFS command tools via the MCP protocol

## Technical Flow

1. **Classification**: Query classified as `mcp_info` in `retriever_graph.py`
2. **Agent Selection**: Routes to `mcp_agent` method
3. **Tool Binding**: Fetches available tools from MCP server via `get_tools()`
4. **Execution**: Uses LLM with tool calling to select and execute appropriate command
5. **Response**: Returns command output to user

## Debugging MCP Agent Triggers

To see which agent is triggered:
- Check logs for classification result (will show "mcp_agent" for MCP)
- Look for "Successfully connected to MCP server" message
- Monitor tool calls being made to the MCP server

## Notes

- MCP agent requires LLMs with tool-calling capabilities (e.g., Llama 3.1, GPT-4)
- If MCP server is unavailable, queries may fall back to RAG agent
- The classification uses either built-in tool calling or prompt-based classification depending on LLM capabilities