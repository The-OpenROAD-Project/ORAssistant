import pytest
import os
import subprocess
from unittest.mock import Mock, patch
from src.openroad_mcp.server.orfs.orfs_base import ORFSBase, _should_skip_gui
from src.openroad_mcp.server.orfs.orfs_tools import ORFS


class TestORFSBase:
    """Test suite for ORFSBase class."""

    @pytest.fixture
    def mock_orfs_server(self, tmp_path):
        """Create a mock ORFS server instance."""
        mock_server = Mock()
        mock_server.platform = None
        mock_server.design = None
        mock_server.flow_dir = str(tmp_path / "flow")
        mock_server.env = os.environ.copy()
        mock_server.cur_stage = 0

        # Create mock stages
        mock_server.stages = {
            0: Mock(info=lambda: "synth"),
            1: Mock(info=lambda: "floorplan"),
            2: Mock(info=lambda: "place"),
            3: Mock(info=lambda: "cts"),
            4: Mock(info=lambda: "route"),
            5: Mock(info=lambda: "final"),
        }
        mock_server.stage_index = {
            "synth": 0,
            "floorplan": 1,
            "place": 2,
            "cts": 3,
            "route": 4,
            "final": 5,
        }

        # Create flow directory
        flow_dir = tmp_path / "flow"
        flow_dir.mkdir(parents=True, exist_ok=True)

        return mock_server

    def test_should_skip_gui_true(self):
        """Test _should_skip_gui returns True when DISABLE_GUI is set."""
        with patch.dict(os.environ, {"DISABLE_GUI": "true"}):
            assert _should_skip_gui() is True

        with patch.dict(os.environ, {"DISABLE_GUI": "1"}):
            assert _should_skip_gui() is True

        with patch.dict(os.environ, {"DISABLE_GUI": "yes"}):
            assert _should_skip_gui() is True

    def test_should_skip_gui_false(self):
        """Test _should_skip_gui returns False when DISABLE_GUI is not set or false."""
        with patch.dict(os.environ, {"DISABLE_GUI": "false"}):
            assert _should_skip_gui() is False

        with patch.dict(os.environ, {}, clear=True):
            # Default should be false
            assert _should_skip_gui() is False

    def test_get_platforms_impl(self, mock_orfs_server):
        """Test _get_platforms_impl sets default platform."""
        ORFS.server = mock_orfs_server
        base = ORFSBase()

        result = base._get_platforms_impl()

        assert result == "sky130hd"
        assert mock_orfs_server.platform == "sky130hd"

    def test_get_designs_impl(self, mock_orfs_server):
        """Test _get_designs_impl sets default design."""
        ORFS.server = mock_orfs_server
        base = ORFSBase()

        result = base._get_designs_impl()

        assert result == "riscv32i"
        assert mock_orfs_server.design == "riscv32i"

    def test_check_configuration_initializes_platform(self, mock_orfs_server):
        """Test _check_configuration initializes platform if not set."""
        ORFS.server = mock_orfs_server
        mock_orfs_server.platform = None
        mock_orfs_server.design = "test_design"
        mock_orfs_server._get_platforms_impl = Mock(return_value="sky130hd")
        mock_orfs_server._get_designs_impl = Mock()

        base = ORFSBase()
        base._check_configuration()

        mock_orfs_server._get_platforms_impl.assert_called_once()
        mock_orfs_server._get_designs_impl.assert_not_called()

    def test_check_configuration_initializes_design(self, mock_orfs_server):
        """Test _check_configuration initializes design if not set."""
        ORFS.server = mock_orfs_server
        mock_orfs_server.platform = "sky130hd"
        mock_orfs_server.design = None
        mock_orfs_server._get_platforms_impl = Mock()
        mock_orfs_server._get_designs_impl = Mock(return_value="riscv32i")

        base = ORFSBase()
        base._check_configuration()

        mock_orfs_server._get_platforms_impl.assert_not_called()
        mock_orfs_server._get_designs_impl.assert_called_once()

    def test_check_configuration_already_set(self, mock_orfs_server):
        """Test _check_configuration does nothing when already configured."""
        ORFS.server = mock_orfs_server
        mock_orfs_server.platform = "sky130hd"
        mock_orfs_server.design = "riscv32i"
        mock_orfs_server._get_platforms_impl = Mock()
        mock_orfs_server._get_designs_impl = Mock()

        base = ORFSBase()
        base._check_configuration()

        mock_orfs_server._get_platforms_impl.assert_not_called()
        mock_orfs_server._get_designs_impl.assert_not_called()

    @patch("subprocess.Popen")
    def test_run_command_success(self, mock_popen, mock_orfs_server):
        """Test _run_command executes successfully."""
        ORFS.server = mock_orfs_server

        # Mock subprocess
        mock_process = Mock()
        mock_process.returncode = 0
        mock_process.stdout = iter(["Line 1\n", "Line 2\n", "Complete\n"])
        mock_process.wait = Mock(return_value=0)
        mock_popen.return_value = mock_process

        base = ORFSBase()
        base._run_command("make synth")

        # Verify subprocess was called
        mock_popen.assert_called_once()
        assert "make synth" in str(mock_popen.call_args)

    @patch("subprocess.Popen")
    def test_run_command_failure(self, mock_popen, mock_orfs_server):
        """Test _run_command raises exception on failure."""
        ORFS.server = mock_orfs_server

        # Mock subprocess failure
        mock_process = Mock()
        mock_process.returncode = 1
        mock_process.stdout = iter(["Error occurred\n"])
        mock_process.wait = Mock(return_value=1)
        mock_popen.return_value = mock_process

        base = ORFSBase()

        with pytest.raises(subprocess.CalledProcessError):
            base._run_command("make synth")

    @patch("subprocess.Popen")
    def test_command_changes_directory(self, mock_popen, mock_orfs_server, tmp_path):
        """Test _command changes to flow directory and back."""
        ORFS.server = mock_orfs_server
        mock_orfs_server.platform = "sky130hd"
        mock_orfs_server.design = "riscv32i"
        mock_orfs_server._run_command = Mock()

        original_dir = os.getcwd()

        base = ORFSBase()
        base._command("synth")

        # Verify we're back in original directory
        assert os.getcwd() == original_dir

        # Verify _run_command was called
        mock_orfs_server._run_command.assert_called_once()

    def test_get_platforms_tool(self, mock_orfs_server):
        """Test get_platforms MCP tool."""
        ORFS.server = mock_orfs_server

        result = ORFSBase.get_platforms()

        assert result == "sky130hd"
        assert mock_orfs_server.platform == "sky130hd"

    def test_get_designs_tool(self, mock_orfs_server):
        """Test get_designs MCP tool."""
        ORFS.server = mock_orfs_server

        result = ORFSBase.get_designs()

        assert result == "riscv32i"
        assert mock_orfs_server.design == "riscv32i"

    def test_make_tool(self, mock_orfs_server):
        """Test make MCP tool."""
        ORFS.server = mock_orfs_server
        mock_orfs_server._check_configuration = Mock()
        mock_orfs_server._command = Mock()

        result = ORFSBase.make("clean")

        mock_orfs_server._check_configuration.assert_called_once()
        mock_orfs_server._command.assert_called_once_with("clean")
        assert result == "finished clean"

    def test_get_stage_names(self, mock_orfs_server):
        """Test get_stage_names MCP tool."""
        ORFS.server = mock_orfs_server

        result = ORFSBase.get_stage_names()

        assert "synth" in result
        assert "floorplan" in result
        assert "place" in result
        assert "cts" in result
        assert "route" in result
        assert "final" in result

    def test_jump_valid_stage(self, mock_orfs_server):
        """Test jump to valid stage."""
        ORFS.server = mock_orfs_server
        mock_orfs_server._check_configuration = Mock()
        mock_orfs_server._command = Mock()

        with patch.dict(os.environ, {"DISABLE_GUI": "true"}):
            result = ORFSBase.jump("floorplan")

        assert result == "finished floorplan"
        assert mock_orfs_server.cur_stage == 1
        mock_orfs_server._command.assert_called_once_with("floorplan")

    def test_jump_invalid_stage(self, mock_orfs_server):
        """Test jump to invalid stage."""
        ORFS.server = mock_orfs_server
        mock_orfs_server._check_configuration = Mock()
        mock_orfs_server._command = Mock()

        result = ORFSBase.jump("invalid_stage")

        assert result == "aborted invalid_stage"
        mock_orfs_server._command.assert_not_called()

    def test_jump_with_gui_enabled(self, mock_orfs_server):
        """Test jump attempts to open GUI when not disabled."""
        ORFS.server = mock_orfs_server
        mock_orfs_server._check_configuration = Mock()
        mock_orfs_server._command = Mock()

        with patch.dict(os.environ, {"DISABLE_GUI": "false"}):
            _result = ORFSBase.jump("synth")

        # Should call both synth and gui_synth
        assert mock_orfs_server._command.call_count == 2
        mock_orfs_server._command.assert_any_call("synth")
        mock_orfs_server._command.assert_any_call("gui_synth")

    def test_jump_gui_failure_doesnt_crash(self, mock_orfs_server):
        """Test jump handles GUI command failure gracefully."""
        ORFS.server = mock_orfs_server
        mock_orfs_server._check_configuration = Mock()

        # Make GUI command fail
        def command_side_effect(cmd):
            if cmd.startswith("gui_"):
                raise subprocess.CalledProcessError(1, cmd)

        mock_orfs_server._command = Mock(side_effect=command_side_effect)

        with patch.dict(os.environ, {"DISABLE_GUI": "false"}):
            result = ORFSBase.jump("synth")

        # Should still return success even though GUI failed
        assert result == "finished synth"

    def test_step_advances_stage(self, mock_orfs_server):
        """Test step advances to next stage."""
        ORFS.server = mock_orfs_server
        mock_orfs_server.cur_stage = 0
        mock_orfs_server._check_configuration = Mock()
        mock_orfs_server._command = Mock()

        with patch.dict(os.environ, {"DISABLE_GUI": "true"}):
            result = ORFSBase.step()

        assert mock_orfs_server.cur_stage == 1
        assert result == "finished floorplan"
        mock_orfs_server._command.assert_called_once_with("floorplan")

    def test_step_at_end_of_pipeline(self, mock_orfs_server):
        """Test step at end of pipeline doesn't advance beyond final stage."""
        ORFS.server = mock_orfs_server
        mock_orfs_server.cur_stage = 5  # Final stage
        mock_orfs_server._check_configuration = Mock()
        mock_orfs_server._command = Mock()

        with patch.dict(os.environ, {"DISABLE_GUI": "true"}):
            result = ORFSBase.step()

        # Should stay at stage 5
        assert mock_orfs_server.cur_stage == 5
        assert result == "finished final"

    def test_step_with_gui_enabled(self, mock_orfs_server):
        """Test step attempts to open GUI when not disabled."""
        ORFS.server = mock_orfs_server
        mock_orfs_server.cur_stage = 0
        mock_orfs_server._check_configuration = Mock()
        mock_orfs_server._command = Mock()

        with patch.dict(os.environ, {"DISABLE_GUI": "false"}):
            _result = ORFSBase.step()

        # Should call both floorplan and gui_floorplan
        assert mock_orfs_server._command.call_count == 2
        mock_orfs_server._command.assert_any_call("floorplan")
        mock_orfs_server._command.assert_any_call("gui_floorplan")

    def test_get_platforms_requires_server(self):
        """Test get_platforms fails without server initialization."""
        ORFS.server = None

        with pytest.raises(AssertionError):
            ORFSBase.get_platforms()

    def test_make_requires_server(self):
        """Test make fails without server initialization."""
        ORFS.server = None

        with pytest.raises(AssertionError):
            ORFSBase.make("synth")
