#!/usr/bin/env python3
import os
import subprocess
import logging
from dotenv import load_dotenv
from mcp.server.fastmcp import FastMCP

load_dotenv()
env = os.environ
mcp = FastMCP("EXEC")



@mcp.tool()
def exec_openroad_gui(command: str) -> str:
    """Open OpenROAD GUI"""
    print(os.environ)
    subprocess.run(f"openroad -gui".split(), env=env)
    return "Launched OpenROAD GUI"

@mcp.tool()
def exec_magic(command: str) -> str:
    """Open Magic VLSI"""
    logging.info("magic")
    print(os.environ)
    run_command("magic")
    return "Launched Magic"

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
def run_command(cmd):
    try:
        result = subprocess.run(cmd.split(), capture_output=True, text=True, check=True, env=env)
        logger.info(f"Command output:\n{result.stdout}")
        if result.stderr:
            logger.warning(f"Command stderr:\n{result.stderr}")
        return result.stdout
    except subprocess.CalledProcessError as e:
        logger.error(f"Command failed with error:\n{e.stderr}")
        raise

if __name__ == "__main__":
    mcp.run(transport="stdio")
