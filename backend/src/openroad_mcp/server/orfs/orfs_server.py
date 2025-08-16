import os
import subprocess
import logging
from dotenv import load_dotenv
from mcp.server.fastmcp import FastMCP
from orfs_tools import ORFS_Tools

load_dotenv()
env = os.environ
flow_dir = os.path.join(os.getenv("ORFS_DIR"), "flow")
mcp = FastMCP("ORFS")

class ORFS(ORFS_Tools):
    @mcp.tool()
    def get_platforms():
        """call get platforms to display possible platforms to run through flow"""
        # TODO: scrape platforms instead of serving only default sky130
        if False:
            pass
        else:
            ORFS.platform = "sky130hd"
            return ORFS.platform

    @mcp.tool()
    def get_designs():
        """call get designs to display possible designs to run through flow"""
        # TODO: scrape designs instead of default riscv
        if False:
            pass
        else:
            ORFS.design = "riscv32i"
            return ORFS.design

    @mcp.tool()
    def make(cmd: str):
        """call make command if query contains make keyword and a single argument"""
        working = os.getcwd()
        os.chdir(flow_dir)

        if not ORFS.platform:
            logging.info(ORFS.get_platforms())

        if not ORFS.design:
            logging.info(ORFS.get_designs())

        make = f"make DESIGN_CONFIG={flow_dir}/designs/{ORFS.platform}/{ORFS.design}/config.mk"
        build_command = make + " " + cmd
        ORFS.run_command(build_command)

        os.chdir(working)
        return f"finished {cmd}"

    @mcp.tool()
    def get_stage_names() -> str:
        """get stage names for possible states this mcp server can be in the chip design pipeline"""
        stage_names = [_.info() for _ in ORFS.stages.values()]
        logging.info(stage_names) # in server process
        # for chatbot output
        result = ""
        for _ in stage_names:
            result += f"{_}\n"
        return result


    @mcp.tool()
    def jump(stage: str) -> str:
        """call jump command if contains jump keyword and stage argument"""
        working = os.getcwd()
        os.chdir(flow_dir)

        if not ORFS.platform:
            logging.info(ORFS.get_platforms())

        if not ORFS.design:
            logging.info(ORFS.get_designs())

        make = f"make DESIGN_CONFIG={flow_dir}/designs/{ORFS.platform}/{ORFS.design}/config.mk"
        stage_names = [_.info() for _ in ORFS.stages.values()]
        logging.info(stage_names)
        if stage in stage_names:
            logging.info(stage)
            build_command = make + " " + stage
            ORFS.cur_stage = ORFS.stage_index[stage]
            ORFS.run_command(build_command)

            build_gui_command = make + " gui_" + stage
            ORFS.run_command(build_gui_command)

            os.chdir(working)
            return f"finished {stage}"
        else:
            logging.info("jump unsuccessful...")
            return f"aborted {stage}"


    @mcp.tool()
    def step() -> str:
        """call step command if contains step keyword to progress through pipeline"""
        def make_keyword():
            logging.info(ORFS.cur_stage)
            if ORFS.cur_stage <= len(ORFS.stages) - 2:
                ORFS.cur_stage += 1
            else:
                logging.info("end of pipeline...")
            return ORFS.stages[ORFS.cur_stage].info()
        working = os.getcwd()
        os.chdir(flow_dir)

        if not ORFS.platform:
            logging.info(ORFS.get_platforms())

        if not ORFS.design:
            logging.info(ORFS.get_designs())

        make = f"make DESIGN_CONFIG={flow_dir}/designs/{ORFS.platform}/{ORFS.design}/config.mk"
        command = make_keyword()
        logging.info(command)
        build_command = make + " " + command
        ORFS.run_command(build_command)

        build_gui_command = make + " gui_" + command
        ORFS.run_command(build_gui_command)

        os.chdir(working)
        return f"finished {command}"

    def run_command(cmd):
        logging.info("start command")

        process = subprocess.Popen(
            cmd.split(),
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            bufsize=1,  # Line-buffered
            universal_newlines=True,  # Text mode
            env=env
        )

        for line in process.stdout:
            logging.info(line.rstrip())

        process.wait()
        if process.returncode != 0:
            logging.error(f"Command exited with return code {process.returncode}")
            raise subprocess.CalledProcessError(process.returncode, cmd)

    # TODO: scrape all makefile keywords and make into mcp tool
    def get_all_keywords(self):
        pass


if __name__ == "__main__":
    mcp.run(transport="streamable-http")
