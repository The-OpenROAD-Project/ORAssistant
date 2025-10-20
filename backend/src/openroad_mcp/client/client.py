import asyncio
import logging
from typing import Any
from datetime import timedelta
from langchain_mcp_adapters.client import MultiServerMCPClient  # type: ignore

MCP_SERVER_URL = "http://localhost:3001/mcp/"

_tools_cache: Any = None


async def get_tools_async() -> Any:
    """Get MCP tools asynchronously"""
    global _tools_cache
    if _tools_cache is None:
        try:
            client = MultiServerMCPClient(
                {
                    "orfs_cmd": {
                        "transport": "streamable_http",
                        "url": MCP_SERVER_URL,
                        # TODO: remove this once tools are async!
                        # HTTP request timeout - increase for long make commands
                        "timeout": timedelta(hours=2),
                        # SSE read timeout - how long to wait for events
                        "sse_read_timeout": timedelta(hours=2),
                    },
                }
            )
            _tools_cache = await client.get_tools()
            logging.info("Successfully connected to MCP server and retrieved tools")
        except Exception as e:
            logging.warning(f"Failed to connect to MCP server: {e}")
            _tools_cache = []
    return _tools_cache


def get_tools() -> Any:
    """Get MCP tools synchronously"""
    try:
        return asyncio.run(get_tools_async())
    except Exception as e:
        logging.warning(f"Failed to connect to MCP server: {e}")
        return []
