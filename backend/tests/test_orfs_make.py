import pytest
import os
from unittest.mock import Mock, patch
from src.openroad_mcp.server.orfs.orfs_make import ORFSMake
from src.openroad_mcp.server.orfs.orfs_tools import ORFS


class TestORFSMake:
    """Test suite for ORFSMake class."""

    @pytest.fixture
    def mock_orfs_server(self, tmp_path):
        """Create a mock ORFS server instance."""
        mock_server = Mock()
        mock_server.platform = "sky130hd"
        mock_server.design = "riscv32i"
        mock_server.flow_dir = str(tmp_path / "flow")
        mock_server.orfs_env = {}
        mock_server.makefile_pointer = None
        mock_server.dynamic_makefile = False

        # Create necessary directory structure
        design_dir = tmp_path / "flow" / "designs" / "sky130hd" / "riscv32i"
        design_dir.mkdir(parents=True, exist_ok=True)

        return mock_server

    def test_get_default_makefile(self, mock_orfs_server):
        """Test _get_default_makefile sets correct path."""
        ORFS.server = mock_orfs_server
        make = ORFSMake()

        make._get_default_makefile()

        expected_path = f"{mock_orfs_server.flow_dir}/designs/{mock_orfs_server.platform}/{mock_orfs_server.design}/config.mk"
        assert mock_orfs_server.makefile_pointer == expected_path

    def test_get_makefile(self, mock_orfs_server):
        """Test _get_makefile returns current pointer."""
        ORFS.server = mock_orfs_server
        mock_orfs_server.makefile_pointer = "/path/to/config.mk"

        make = ORFSMake()
        result = make._get_makefile()

        assert result == "/path/to/config.mk"

    def test_get_default_env(self, mock_orfs_server):
        """Test _get_default_env initializes standard variables."""
        ORFS.server = mock_orfs_server
        make = ORFSMake()

        make._get_default_env()

        # Check required variables are set
        assert "PLATFORM" in mock_orfs_server.orfs_env
        assert "DESIGN_NAME" in mock_orfs_server.orfs_env
        assert "DESIGN_NICKNAME" in mock_orfs_server.orfs_env
        assert "VERILOG_FILES" in mock_orfs_server.orfs_env
        assert "SDC_FILE" in mock_orfs_server.orfs_env
        assert "CORE_UTILIZATION" in mock_orfs_server.orfs_env
        assert "PLACE_DENSITY" in mock_orfs_server.orfs_env

        # Check values match server config
        assert mock_orfs_server.orfs_env["PLATFORM"] == "sky130hd"
        assert mock_orfs_server.orfs_env["DESIGN_NAME"] == "riscv32i"
        assert mock_orfs_server.orfs_env["CORE_UTILIZATION"] == "50"

    def test_create_dynamic_makefile_no_env_vars(self, mock_orfs_server):
        """Test create_dynamic_makefile returns 'no env vars' when environment is empty."""
        ORFS.server = mock_orfs_server
        mock_orfs_server.orfs_env = {}

        # Access the underlying function from the FunctionTool
        result = ORFSMake.create_dynamic_makefile("test")

        assert result == "no env vars"

    def test_create_dynamic_makefile_with_env_vars(self, mock_orfs_server, tmp_path):
        """Test create_dynamic_makefile writes file with environment variables."""
        ORFS.server = mock_orfs_server
        mock_orfs_server.orfs_env = {
            "PLATFORM": "sky130hd",
            "DESIGN_NAME": "riscv32i",
            "CORE_UTILIZATION": "50",
        }

        result = ORFSMake.create_dynamic_makefile("test")

        # Check dynamic_makefile flag is set
        assert mock_orfs_server.dynamic_makefile is True

        # Check makefile_pointer is set
        expected_path = f"{mock_orfs_server.flow_dir}/designs/{mock_orfs_server.platform}/{mock_orfs_server.design}/dynamic_config.mk"
        assert mock_orfs_server.makefile_pointer == expected_path

        # Check file was created
        assert os.path.exists(expected_path)

        # Check file contents
        with open(expected_path, "r") as f:
            content = f.read()
            assert "export PLATFORM = sky130hd" in content
            assert "export DESIGN_NAME = riscv32i" in content
            assert "export CORE_UTILIZATION = 50" in content

        # Check result format
        assert "PLATFORM: sky130hd" in result
        assert "DESIGN_NAME: riscv32i" in result
        assert "CORE_UTILIZATION: 50" in result

    def test_create_dynamic_makefile_initializes_design_platform(
        self, mock_orfs_server
    ):
        """Test create_dynamic_makefile initializes design/platform if not set."""
        ORFS.server = mock_orfs_server
        mock_orfs_server.platform = None
        mock_orfs_server.design = None
        mock_orfs_server.orfs_env = {"TEST": "value"}

        # Mock the initialization methods
        mock_orfs_server._get_designs_impl = Mock()
        mock_orfs_server._get_platforms_impl = Mock()
        mock_orfs_server._get_default_env = Mock()

        # Set values after init calls
        def set_platform():
            mock_orfs_server.platform = "sky130hd"

        def set_design():
            mock_orfs_server.design = "riscv32i"

        mock_orfs_server._get_platforms_impl.side_effect = set_platform
        mock_orfs_server._get_designs_impl.side_effect = set_design

        _result = ORFSMake.create_dynamic_makefile("test")

        # Verify initialization was called
        mock_orfs_server._get_designs_impl.assert_called_once()
        mock_orfs_server._get_platforms_impl.assert_called_once()
        mock_orfs_server._get_default_env.assert_called_once()

    @patch("src.openroad_mcp.server.orfs.orfs_make.JsonOutputParser")
    @patch("src.openroad_mcp.server.orfs.orfs_make.ChatPromptTemplate")
    def test_get_env_vars_success(
        self, mock_prompt_template, mock_json_parser, mock_orfs_server
    ):
        """Test get_env_vars extracts variables from LLM."""
        ORFS.server = mock_orfs_server
        ORFS.llm = Mock()

        # Mock initialization methods
        mock_orfs_server._get_designs_impl = Mock()
        mock_orfs_server._get_platforms_impl = Mock()
        mock_orfs_server._get_default_env = Mock()
        mock_orfs_server.retrieve_general = Mock(
            return_value=["documentation context", []]
        )

        # Mock the LLM chain
        mock_chain = Mock()
        mock_chain.invoke.return_value = {
            "CLOCK_PERIOD": "10.0",
            "CORE_UTILIZATION": "60",
        }

        # Setup chain building
        mock_prompt_template.from_template.return_value.__or__ = Mock(
            return_value=Mock(__or__=Mock(return_value=mock_chain))
        )

        result = ORFSMake.get_env_vars("get clock and utilization variables")

        # Check return value
        assert result == "done env"

        # Verify environment was updated
        assert "CLOCK_PERIOD" in mock_orfs_server.orfs_env
        assert "CORE_UTILIZATION" in mock_orfs_server.orfs_env
        assert mock_orfs_server.orfs_env["CLOCK_PERIOD"] == "10.0"
        assert mock_orfs_server.orfs_env["CORE_UTILIZATION"] == "60"

    def test_get_env_vars_requires_server(self):
        """Test get_env_vars fails without server initialization."""
        ORFS.server = None

        with pytest.raises(AssertionError):
            ORFSMake.get_env_vars("test")

    def test_get_env_vars_requires_llm(self, mock_orfs_server):
        """Test get_env_vars fails without LLM initialization."""
        ORFS.server = mock_orfs_server
        ORFS.llm = None

        with pytest.raises(AssertionError):
            ORFSMake.get_env_vars("test")

    def test_create_dynamic_makefile_with_makefile_syntax(
        self, mock_orfs_server, tmp_path
    ):
        """Test that create_dynamic_makefile preserves Makefile syntax like $(shell ...)."""
        ORFS.server = mock_orfs_server
        mock_orfs_server.orfs_env = {
            "PLATFORM": "asap7",
            "CORE_AREA": "$(shell export VAR=1 && echo 100)",  # Legitimate Makefile syntax
            "DIE_AREA": "$(PLATFORM_DIR)/$(DESIGN_NAME)",  # Variable reference
        }

        _result = ORFSMake.create_dynamic_makefile("test")

        # Check file was created
        expected_path = f"{mock_orfs_server.flow_dir}/designs/{mock_orfs_server.platform}/{mock_orfs_server.design}/dynamic_config.mk"
        assert os.path.exists(expected_path)

        # Verify Makefile syntax is preserved
        with open(expected_path, "r") as f:
            content = f.read()
            assert "export CORE_AREA = $(shell export VAR=1 && echo 100)" in content
            assert "export DIE_AREA = $(PLATFORM_DIR)/$(DESIGN_NAME)" in content
