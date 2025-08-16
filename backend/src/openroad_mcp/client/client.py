import os
import asyncio
from langchain_mcp_adapters.client import MultiServerMCPClient  # type: ignore

# TODO: only supports other LLMs with tool-chain capabilities like llama 3.1

mcp_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
client = MultiServerMCPClient(
    {
        "orfs_cmd": {
            "transport": "streamable_http",
            "url": "http://localhost:8000/mcp/",
        },
    }
)
tools = asyncio.run(client.get_tools())
