import logging
from src.openroad_mcp.server.orfs.orfs_tools import ORFS
from langchain.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from src.prompts.prompt_templates import env_prompt_template


class ORFSMake(ORFS):
    """Handles dynamic Makefile generation and environment configuration for ORFS.

    This class manages the creation of dynamic Makefile configurations and environment
    variables for OpenROAD-flow-scripts builds. It provides MCP tools for generating
    config.mk files and extracting environment variables from documentation using
    RAG (Retrieval-Augmented Generation).
    """

    def _get_default_makefile(self) -> None:
        """Set the makefile pointer to the default config.mk location."""
        assert ORFS.server is not None
        ORFS.server.makefile_pointer = f"{ORFS.server.flow_dir}/designs/{ORFS.server.platform}/{ORFS.server.design}/config.mk"

    def _get_makefile(self) -> None:
        """Retrieve the current makefile pointer path."""
        assert ORFS.server is not None
        if ORFS.server.makefile_pointer:
            return ORFS.server.makefile_pointer

    def _get_default_env(self) -> None:
        """Initialize default environment variables for ORFS build configuration."""
        # TODO: categorize into ORFSEnv TypedDict
        assert ORFS.server is not None
        ORFS.server.orfs_env.update(
            {
                "PLATFORM": f"{ORFS.server.platform}",
                "DESIGN_NAME": f"{ORFS.server.design}",
                "DESIGN_NICKNAME": f"{ORFS.server.design}",
                "VERILOG_FILES": "$(sort $(wildcard ./designs/src/$(DESIGN_NICKNAME)/*.v))",
                "SDC_FILE": "./designs/$(PLATFORM)/$(DESIGN_NICKNAME)/constraint.sdc",
                "CORE_UTILIZATION": "50",
                "PLACE_DENSITY": "50",
            }
        )

    @staticmethod
    @ORFS.mcp.tool
    def create_dynamic_makefile(cmd: str) -> str:
        """Create a dynamic Makefile configuration for the current ORFS design.

        Generates a dynamic_config.mk file containing exported environment variables
        for the OpenROAD-flow-scripts build system. This enables custom build
        configurations without modifying the default config.mk files.

        The tool ensures a design and platform are selected (prompting initialization
        if needed), then creates a Makefile with all current environment variables
        exported in the format: `export VAR_NAME = value`

        Args:
            cmd: User command or query string (currently unused - may be used for
                 future query-based configuration).

        Returns:
            str: A formatted string listing all environment variables and their values,
                 one per line in the format "VAR_NAME: value". Returns "no env vars"
                 if no environment variables are configured.

        Side Effects:
            - Sets ORFS.server.dynamic_makefile to True
            - Creates/overwrites dynamic_config.mk in the design directory
            - Updates ORFS.server.makefile_pointer to the dynamic config path
            - May trigger design/platform initialization if not already set
            - Logs warning if no design/platform is selected

        Example:
            >>> create_dynamic_makefile("setup build config")
            "PLATFORM: asap7\\nDESIGN_NAME: gcd\\nCORE_UTILIZATION: 50\\n..."

        Note:
            File is written to: {flow_dir}/designs/{platform}/{design}/dynamic_config.mk
        """
        assert ORFS.server is not None
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

    @staticmethod
    @ORFS.mcp.tool
    def get_env_vars(cmd: str) -> str:
        """Extract environment variables from ORFS documentation using RAG.

        Uses Retrieval-Augmented Generation (RAG) to search ORFS documentation
        for relevant environment variables based on a user query, then uses an
        LLM to parse and extract them in Makefile export format. The extracted
        variables are automatically added to the current environment configuration.

        This tool is useful for discovering and applying environment variables
        from documentation without manual lookup.

        Args:
            cmd: Natural language query describing what environment variables
                 are needed (e.g., "variables for clock period and frequency").

        Returns:
            str: Always returns "done env" to indicate completion. Check logs
                 for detailed information about retrieved variables.

        Side Effects:
            - Initializes design and platform if not already set
            - Queries RAG system for relevant documentation
            - Invokes LLM chain to parse environment variables from context
            - Updates ORFS.server.orfs_env with extracted variables
            - Logs retrieved context, parsed variables, and variable types

        Example:
            >>> get_env_vars("get clock period and frequency variables")
            "done env"
            # ORFS.server.orfs_env now updated with CLOCK_PERIOD, CLOCK_FREQ, etc.

        Note:
            The LLM is prompted to output only valid Makefile export statements
            in the format: `export {env_name} = {env_value}`
        """
        assert ORFS.server is not None
        assert ORFS.llm is not None
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
        ans = env_chain.invoke({"context": result[0], "question": string + cmd})
        logging.info(result[0])
        logging.info(ans)
        ORFS.server.orfs_env.update(ans)
        logging.info(type(ans))
        return "done env"
