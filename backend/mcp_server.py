import os
import logging

from src.openroad_mcp.server.orfs.orfs_server import ORFSServer

logging.basicConfig(
    level=os.environ.get("LOGLEVEL", "INFO").upper(),
    format="%(asctime)s [%(levelname)s] %(filename)s:%(lineno)d - %(message)s\n"
)

server = ORFSServer()
server.mcp.run(transport="http", host="127.0.0.1", port=3001)
