import os
import logging

logging.basicConfig(
    level=os.environ.get("LOGLEVEL", "INFO").upper(),
    format="%(asctime)s [%(levelname)s] %(filename)s:%(lineno)d - %(message)s\n"
)

from typing import TypedDict, Tuple
from dotenv import load_dotenv

from .pipeline import Synthesis, Floorplan, Placement, CTS, Routing, FinalReport
from src.openroad_mcp.server.orfs.orfs_tools import ORFS
from src.openroad_mcp.server.orfs.orfs_make import ORFSMake
from src.openroad_mcp.server.orfs.orfs_base import ORFSBase
from src.openroad_mcp.server.orfs.orfs_rag import ORFSRag


class ORFSEnv(TypedDict):
    general: list[str|None]

    synthesis: list[str|None]
    floorplan: list[str|None]
    placement: list[str|None]
    cts: list[str|None]
    routing: list[str|None]


class ORFSServer(ORFSBase, ORFSMake, ORFSRag):
    def __init__(self):
        ORFS.server = self

        self.design: str | None = None
        self.platform: str | None = None
        self.command: str | None = None
        self.makefile_pointer: str | None = None

        self.orfs_env: dict = ORFSEnv()

        self.design_list: list[str] = []
        self.stages: dict[int, Any] = {
            0: Synthesis(),
            1: Floorplan(),
            2: Placement(),
            3: CTS(),
            4: Routing(),
            5: FinalReport(),
        }
        self.stage_index: dict[str, int] = {v.info(): k for k, v in self.stages.items()}

        self.cur_stage: int = -1

        self._setup_env()
        logging.warning("instantiated...")

    def _setup_env(self):
        load_dotenv()
        self.env = os.environ
        self.orfs_dir: str | None = os.getenv("ORFS_DIR")
        if self.orfs_dir is None:
            raise ValueError("ORFS_DIR environment variable is not set")
        self.flow_dir = os.path.join(self.orfs_dir, "flow")

if __name__ == "__main__":
    server = ORFSServer()
    server.mcp.run(transport="http", host="127.0.0.1", port=3001)
