import logging
from orfs_tools import ORFS
from langchain.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from chains.prompts.prompt_templates import env_prompt_template


class ORFSMake(ORFS):
    def _get_default_makefile(self) -> str:
        ORFS.server.makefile_pointer = f"{ORFS.server.flow_dir}/designs/{ORFS.server.platform}/{ORFS.server.design}/config.mk"
    def _get_makefile(self) -> str:
        if ORFS.server.makefile_pointer:
            return ORFS.server.makefile_pointer
    def _get_default_env(self):
        # TODO: categorize into ORFSEnv TypedDict
        ORFS.server.orfs_env.update({
            "PLATFORM": f"{ORFS.server.platform}",
            "DESIGN_NAME": f"{ORFS.server.design}",
            "DESIGN_NICKNAME": f"{ORFS.server.design}",
            "VERILOG_FILES": f"$(sort $(wildcard ./designs/src/$(DESIGN_NICKNAME)/*.v))",
            "SDC_FILE": f"./designs/$(PLATFORM)/$(DESIGN_NICKNAME)/constraint.sdc",
            "CORE_UTILIZATION": "50",
            "PLACE_DENSITY": "50",
        })

    @ORFS.mcp.tool
    def create_dynamic_makefile(cmd: str):
        "Create a dynamic makefile and return results"
        if not (ORFS.server.design and ORFS.server.platform):
            logging.warning("no custom design/platform selected!")
            ORFS.server._get_designs_impl()
            ORFS.server._get_platforms_impl()
            ORFS.server._get_default_env()
        else:
            pass

        ORFS.server.dynamic_makefile = True
        ORFS.server.makefile_pointer = f"{ORFS.server.flow_dir}/designs/{ORFS.server.platform}/{ORFS.server.design}/dynamic_config.mk"
        with open(f"{ORFS.server.makefile_pointer}", "w") as f:
            for key in ORFS.server.orfs_env.keys():
                f.write(f"export {key} = {ORFS.server.orfs_env[key]}\n")
        result = ""
        for key in ORFS.server.orfs_env.keys():
            result += f"{key}: {ORFS.server.orfs_env[key]}\n"
        if result:
            return result
        else:
            return "no env vars"

    @ORFS.mcp.tool
    def get_env_vars(cmd: str):
        "Pass query to RAG retrieval tools to get environment variables"
        ORFS.server._get_designs_impl()
        ORFS.server._get_platforms_impl()
        ORFS.server._get_default_env()
        result = ORFS.server.retrieve_general(cmd)
        logging.info(ORFS.llm)
        env_chain = (
            ChatPromptTemplate.from_template(env_prompt_template)
            | ORFS.llm
            | JsonOutputParser()
        )
        string = "Only output environment variables in the following format:\n export {env_name} = {env_value}\n"
        ans = env_chain.invoke({"context": result[0], "question": string+cmd})
        logging.info(result[0])
        logging.info(ans)
        ORFS.server.orfs_env.update(ans)
        logging.info(type(ans))
        return "done env"
