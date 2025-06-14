#!/usr/bin/env python3

import os
import subprocess
import logging
from dotenv import load_dotenv
from mcp.server.fastmcp import FastMCP

load_dotenv()
env = os.environ
mcp = FastMCP("ORFS")

@mcp.tool()
def run_orfs_cmd(command: str, design: str) -> None:
    """Open OpenROAD GUI"""
    working = os.getcwd()
    os.chdir(os.path.expanduser("/home/flow/OpenROAD-flow-scripts/flow"))

    make = "make DESIGN_CONFIG=/home/flow/OpenROAD-flow-scripts/flow/designs/{}/{}/config.mk".format("sky130hd", design)
    build_command = make + " " + command
    print(build_command)
    #subprocess.run(build_command.split(), env=env, stdout=sys.stdout, stderr=sys.stderr )
    run_command(build_command)

    os.chdir(working)

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
def run_command(cmd):
    process = subprocess.Popen(
        cmd.split(),
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        bufsize=1,  # Line-buffered
        universal_newlines=True,  # Text mode
        env=env
    )

    for line in process.stdout:
        logger.info(line.rstrip())

    process.wait()
    if process.returncode != 0:
        logger.error(f"Command exited with return code {process.returncode}")
        raise subprocess.CalledProcessError(process.returncode, cmd)

if __name__ == "__main__":
    mcp.run(transport="stdio")
    #Top()
    #run_test()
