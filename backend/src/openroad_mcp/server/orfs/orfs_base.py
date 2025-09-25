import os
import subprocess
import logging
from orfs_tools import ORFS

class ORFSBase(ORFS):
    def _get_platforms_impl(self) -> str:
        """Internal implementation of get_platforms"""
        # TODO: scrape platforms instead of serving only default sky130
        if False:
            pass
        else:
            ORFS.server.platform = "sky130hd"
            return ORFS.server.platform

    def _get_designs_impl(self) -> str:
        """Internal implementation of get_designs"""
        # TODO: scrape designs instead of default riscv
        if False:
            pass
        else:
            ORFS.server.design = "riscv32i"
            return ORFS.server.design

    def _check_configuration(self) -> str:
        if not ORFS.server.platform:
            platform = ORFS.server._get_platforms_impl()
            logging.info(ORFS.server.platform)

        if not ORFS.server.design:
            design = ORFS.server._get_designs_impl()
            logging.info(ORFS.server.design)

    def _command(self, cmd) -> str:
        working = os.getcwd()
        os.chdir(ORFS.server.flow_dir)

        make = f"make DESIGN_CONFIG={ORFS.server.flow_dir}/designs/{ORFS.server.platform}/{ORFS.server.design}/config.mk"
        logging.info(cmd)
        build_command = f"{make} {cmd}"
        ORFS.server._run_command(build_command)

        os.chdir(working)

    def _run_command(self, cmd: str) -> None:
        logging.info("start command")

        process = subprocess.Popen(
            cmd.split(),
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            bufsize=1,  # Line-buffered
            universal_newlines=True,  # Text mode
            env=ORFS.server.env,
        )

        if process.stdout:
            for line in process.stdout:
                logging.info(line.rstrip())

        process.wait()
        if process.returncode != 0:
            logging.error(f"Command exited with return code {process.returncode}")
            raise subprocess.CalledProcessError(process.returncode, cmd)

    ### mcp tool section ###

    @ORFS.mcp.tool
    def get_platforms() -> str:
        """call get platforms to display possible platforms to run through flow"""
        return ORFS.server._get_platforms_impl()

    @ORFS.mcp.tool
    def get_designs() -> str:
        """call get designs to display possible designs to run through flow"""
        return ORFS.server._get_designs_impl()

    @ORFS.mcp.tool
    def make(cmd: str) -> str:
        """call make command if query contains make keyword and a single argument"""

        ORFS.server._check_configuration()
        ORFS.server._command(cmd)

        return f"finished {cmd}"

    @ORFS.mcp.tool
    def get_stage_names() -> str:
        """get stage names for possible states this mcp server can be in the chip design pipeline"""
        stage_names = [_.info() for _ in ORFS.server.stages.values()]
        logging.info(stage_names)  # in server process
        # for chatbot output
        result = ""
        for _ in stage_names:
            result += f"{_}\n"
        return result

    @ORFS.mcp.tool
    def jump(stage: str) -> str:
        """call jump command if contains jump keyword and stage argument"""
        ORFS.server._check_configuration()

        stage_names = [_.info() for _ in ORFS.server.stages.values()]
        logging.info(stage_names)
        if stage in stage_names:
            logging.info(stage)
            ORFS.server.cur_stage = ORFS.server.stage_index[stage]

            ORFS.server._command(stage)
            ORFS.server._command(f"gui_{stage}")

            return f"finished {stage}"
        else:
            logging.info("jump unsuccessful..")
            return f"aborted {stage}"

    @ORFS.mcp.tool
    def step(cmd: str) -> str:
        """call step command if contains step keyword to progress through pipeline"""

        def make_keyword():
            logging.info(ORFS.server.cur_stage)
            if ORFS.server.cur_stage <= len(ORFS.server.stages) - 2:
                ORFS.server.cur_stage += 1
            else:
                logging.info("end of pipeline..")
            return ORFS.server.stages[ORFS.server.cur_stage].info()

        ORFS.server._check_configuration()

        command = make_keyword()
        ORFS.server._command(command)
        ORFS.server._command(f"gui_{command}")
        return f"finished {command}"


    # TODO: scrape all makefile keywords and make into mcp tool
    def get_all_keywords() -> None:
        pass
