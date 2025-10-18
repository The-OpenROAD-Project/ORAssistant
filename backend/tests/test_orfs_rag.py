import pytest
from unittest.mock import Mock, patch
from src.openroad_mcp.server.orfs.orfs_tools import ORFS


class TestORFSRag:
    """Test suite for ORFSRag retrieval methods."""

    @pytest.fixture(autouse=True)
    def setup_orfs(self):
        """Setup ORFS class attributes before each test."""
        # Save original values
        self.original_general = ORFS.general_retriever
        self.original_commands = ORFS.commands_retriever
        self.original_install = ORFS.install_retriever
        self.original_errinfo = ORFS.errinfo_retriever
        self.original_yosys = ORFS.yosys_rtdocs_retriever
        self.original_klayout = ORFS.klayout_retriever

        yield

        # Restore original values
        ORFS.general_retriever = self.original_general
        ORFS.commands_retriever = self.original_commands
        ORFS.install_retriever = self.original_install
        ORFS.errinfo_retriever = self.original_errinfo
        ORFS.yosys_rtdocs_retriever = self.original_yosys
        ORFS.klayout_retriever = self.original_klayout

    @patch("src.openroad_mcp.server.orfs.orfs_rag.format_docs")
    def test_retrieve_general_success(self, mock_format_docs):
        """Test retrieve_general returns formatted docs."""
        # Import after ORFS is set up
        from src.openroad_mcp.server.orfs.orfs_rag import ORFSRag

        # Mock retriever
        mock_retriever = Mock()
        mock_docs = [Mock(), Mock()]
        mock_retriever.invoke.return_value = mock_docs
        ORFS.general_retriever = mock_retriever

        # Mock format_docs
        mock_format_docs.return_value = (
            "formatted text",
            ["source1"],
            ["title1"],
            ["link1"],
        )

        result = ORFSRag.retrieve_general("test query")

        # Verify retriever was called
        mock_retriever.invoke.assert_called_once_with(input="test query")

        # Verify format_docs was called with docs
        mock_format_docs.assert_called_once_with(mock_docs)

        # Verify result
        assert result == ("formatted text", ["source1"], ["title1"], ["link1"])

    def test_retrieve_general_not_initialized(self):
        """Test retrieve_general raises error when retriever not initialized."""
        from src.openroad_mcp.server.orfs.orfs_rag import ORFSRag

        ORFS.general_retriever = None

        with pytest.raises(ValueError, match="General Retriever not initialized"):
            ORFSRag.retrieve_general("test query")

    @patch("src.openroad_mcp.server.orfs.orfs_rag.format_docs")
    def test_retrieve_cmds_success(self, mock_format_docs):
        """Test retrieve_cmds returns formatted docs."""
        from src.openroad_mcp.server.orfs.orfs_rag import ORFSRag

        # Mock retriever
        mock_retriever = Mock()
        mock_docs = [Mock(), Mock()]
        mock_retriever.invoke.return_value = mock_docs
        ORFS.commands_retriever = mock_retriever

        # Mock format_docs
        mock_format_docs.return_value = (
            "formatted text",
            ["source1"],
            ["title1"],
            ["link1"],
        )

        result = ORFSRag.retrieve_cmds("make command")

        # Verify retriever was called
        mock_retriever.invoke.assert_called_once_with(input="make command")

        # Verify result
        assert result == ("formatted text", ["source1"], ["title1"], ["link1"])

    def test_retrieve_cmds_not_initialized(self):
        """Test retrieve_cmds raises error when retriever not initialized."""
        from src.openroad_mcp.server.orfs.orfs_rag import ORFSRag

        ORFS.commands_retriever = None

        with pytest.raises(ValueError, match="Commands Retriever not initialized"):
            ORFSRag.retrieve_cmds("test query")

    @patch("src.openroad_mcp.server.orfs.orfs_rag.format_docs")
    def test_retrieve_install_success(self, mock_format_docs):
        """Test retrieve_install returns formatted docs."""
        from src.openroad_mcp.server.orfs.orfs_rag import ORFSRag

        # Mock retriever
        mock_retriever = Mock()
        mock_docs = [Mock()]
        mock_retriever.invoke.return_value = mock_docs
        ORFS.install_retriever = mock_retriever

        # Mock format_docs
        mock_format_docs.return_value = (
            "formatted text",
            ["source1"],
            ["title1"],
            ["link1"],
        )

        result = ORFSRag.retrieve_install("installation steps")

        # Verify retriever was called
        mock_retriever.invoke.assert_called_once_with(input="installation steps")

        # Verify result
        assert result == ("formatted text", ["source1"], ["title1"], ["link1"])

    def test_retrieve_install_not_initialized(self):
        """Test retrieve_install raises error when retriever not initialized."""
        from src.openroad_mcp.server.orfs.orfs_rag import ORFSRag

        ORFS.install_retriever = None

        with pytest.raises(ValueError, match="Install Retriever not initialized"):
            ORFSRag.retrieve_install("test query")

    @patch("src.openroad_mcp.server.orfs.orfs_rag.format_docs")
    def test_retrieve_errinfo_success(self, mock_format_docs):
        """Test retrieve_errinfo returns formatted docs."""
        from src.openroad_mcp.server.orfs.orfs_rag import ORFSRag

        # Mock retriever
        mock_retriever = Mock()
        mock_docs = [Mock()]
        mock_retriever.invoke.return_value = mock_docs
        ORFS.errinfo_retriever = mock_retriever

        # Mock format_docs
        mock_format_docs.return_value = (
            "formatted text",
            ["source1"],
            ["title1"],
            ["link1"],
        )

        result = ORFSRag.retrieve_errinfo("ANT-0001")

        # Verify retriever was called
        mock_retriever.invoke.assert_called_once_with(input="ANT-0001")

        # Verify result
        assert result == ("formatted text", ["source1"], ["title1"], ["link1"])

    def test_retrieve_errinfo_not_initialized(self):
        """Test retrieve_errinfo raises error when retriever not initialized."""
        from src.openroad_mcp.server.orfs.orfs_rag import ORFSRag

        ORFS.errinfo_retriever = None

        with pytest.raises(ValueError, match="Error Info Retriever not initialized"):
            ORFSRag.retrieve_errinfo("test query")

    @patch("src.openroad_mcp.server.orfs.orfs_rag.format_docs")
    def test_retrieve_yosys_rtdocs_success(self, mock_format_docs):
        """Test retrieve_yosys_rtdocs returns formatted docs."""
        from src.openroad_mcp.server.orfs.orfs_rag import ORFSRag

        # Mock retriever
        mock_retriever = Mock()
        mock_docs = [Mock()]
        mock_retriever.invoke.return_value = mock_docs
        ORFS.yosys_rtdocs_retriever = mock_retriever

        # Mock format_docs
        mock_format_docs.return_value = (
            "formatted text",
            ["source1"],
            ["title1"],
            ["link1"],
        )

        result = ORFSRag.retrieve_yosys_rtdocs("yosys synthesis")

        # Verify retriever was called
        mock_retriever.invoke.assert_called_once_with(input="yosys synthesis")

        # Verify result
        assert result == ("formatted text", ["source1"], ["title1"], ["link1"])

    def test_retrieve_yosys_rtdocs_not_initialized(self):
        """Test retrieve_yosys_rtdocs raises error when retriever not initialized."""
        from src.openroad_mcp.server.orfs.orfs_rag import ORFSRag

        ORFS.yosys_rtdocs_retriever = None

        with pytest.raises(ValueError, match="Yosys RTDocs Retriever not initialized"):
            ORFSRag.retrieve_yosys_rtdocs("test query")

    @patch("src.openroad_mcp.server.orfs.orfs_rag.format_docs")
    def test_retrieve_klayout_docs_success(self, mock_format_docs):
        """Test retrieve_klayout_docs returns formatted docs."""
        from src.openroad_mcp.server.orfs.orfs_rag import ORFSRag

        # Mock retriever
        mock_retriever = Mock()
        mock_docs = [Mock()]
        mock_retriever.invoke.return_value = mock_docs
        ORFS.klayout_retriever = mock_retriever

        # Mock format_docs
        mock_format_docs.return_value = (
            "formatted text",
            ["source1"],
            ["title1"],
            ["link1"],
        )

        result = ORFSRag.retrieve_klayout_docs("klayout usage")

        # Verify retriever was called
        mock_retriever.invoke.assert_called_once_with(input="klayout usage")

        # Verify result
        assert result == ("formatted text", ["source1"], ["title1"], ["link1"])

    def test_retrieve_klayout_docs_not_initialized(self):
        """Test retrieve_klayout_docs raises error when retriever not initialized."""
        from src.openroad_mcp.server.orfs.orfs_rag import ORFSRag

        ORFS.klayout_retriever = None

        with pytest.raises(ValueError, match="KLayout Retriever not initialized"):
            ORFSRag.retrieve_klayout_docs("test query")
