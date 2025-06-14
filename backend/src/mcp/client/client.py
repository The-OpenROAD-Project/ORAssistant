#!/usr/bin/env python3
import os
import asyncio
from langchain_mcp_adapters.client import MultiServerMCPClient

# TODO: only supports other LLMs with tool-chain capabilities like llama 3.1

mcp_path = os.path.dirname(os.path.abspath(__file__)) + "/.."
client = MultiServerMCPClient(
        {
                "exec_cmd": {
                        "command": "python",
                        "args": [f"{mcp_path}/server/exec_server.py"],
                        "transport": "stdio",
                },
                "orfs_cmd": {
                        "command": "python",
                        "args": [f"{mcp_path}/server/orfs_server.py"],
                        "transport": "stdio",
                },
        }
)
tools = asyncio.run(client.get_tools())

