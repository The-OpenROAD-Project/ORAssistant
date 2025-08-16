from .pipeline import Synthesis, Floorplan, Placement, CTS, Routing, FinalReport
from typing import Any


# Global variables and functions for ORFS class
class ORFSTools:
    design: str | None = None
    platform: str | None = None
    command: str | None = None

    design_list: list[str] = []

    stages: dict[int, Any] = {
        0: Synthesis(),
        1: Floorplan(),
        2: Placement(),
        3: CTS(),
        4: Routing(),
        5: FinalReport(),
    }
    stage_index: dict[str, int] = {v.info(): k for k, v in stages.items()}

    cur_stage: int = -1
