import os
import asyncio
import logging
import httpx
from langchain_mcp_adapters.client import MultiServerMCPClient  # type: ignore

# TODO: only supports other LLMs with tool-chain capabilities like llama 3.1
MCP_SERVER_URL = "http://localhost:3001/mcp/"


async def check_mcp_server_health() -> bool:
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            # Health endpoint is at root level, not under /mcp/
            base_url = MCP_SERVER_URL.replace("/mcp/", "")
            response = await client.get(base_url.rstrip("/") + "/health")
            return response.status_code == 200
    except Exception:
        return False


mcp_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")

tools = None


def get_tools():
    global tools
    if tools is None:
        try:
            if asyncio.run(check_mcp_server_health()):
                client = MultiServerMCPClient(
                    {
                        "orfs_cmd": {
                            "transport": "streamable_http",
                            "url": MCP_SERVER_URL,
                        },
                    }
                )
                tools = asyncio.run(client.get_tools())
                logging.info("Successfully connected to MCP server")
            else:
                logging.warning("MCP server health check failed - server not available")
                tools = []
        except Exception as e:
            logging.warning(f"Failed to initialize MCP tools: {e}")
            tools = []
    return tools
