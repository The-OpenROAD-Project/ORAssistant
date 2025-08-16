import os
import logging
from dotenv import load_dotenv
from mcp.server.fastmcp import FastMCP
from pipeline import Synthesis, Floorplan, Placement, CTS, Routing, Final_Report

# Global variables and functions for ORFS class
class ORFS_Tools():

    design = None
    platform = None
    command = None

    design_list = []

    stages = {
        0: Synthesis(),
        1: Floorplan(),
        2: Placement(),
        3: CTS(),
        4: Routing(),
        5: Final_Report(),
    }
    stage_index = {v.info(): k for k, v in stages.items()}

    cur_stage = -1
