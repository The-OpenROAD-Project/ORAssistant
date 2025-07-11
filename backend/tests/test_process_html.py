import pytest
import tempfile
from unittest.mock import patch, Mock, mock_open
from pathlib import Path

from src.tools.process_html import process_html


class TestProcessHTML:
    """Test suite for process_html utility function."""

    def test_process_html_empty_folder(self):
        """Test processing empty folder returns empty list."""
        with tempfile.TemporaryDirectory() as temp_dir:
            result = process_html(temp_dir)
            assert result == []

    def test_process_html_nonexistent_folder(self):
        """Test processing nonexistent folder returns empty list."""
        result = process_html("/nonexistent/folder")
        assert result == []

    @patch("src.tools.process_html.glob.glob")
    @patch("src.tools.process_html.UnstructuredHTMLLoader")
    @patch(
        "builtins.open",
        new_callable=mock_open,
        read_data='{"test.html": "https://example.com"}',
    )
    @patch("src.tools.process_html.os.path.exists")
    @patch("src.tools.process_html.os.listdir")
    def test_process_html_without_splitting(
        self, mock_listdir, mock_exists, mock_file, mock_loader, mock_glob
    ):
        """Test processing HTML without text splitting."""
        # Setup mocks
        mock_exists.return_value = True
        mock_listdir.return_value = ["test.html"]
        mock_glob.return_value = ["./test.html"]

        mock_doc = Mock()
        mock_doc.metadata = {"source": "test.html"}
        mock_doc.page_content = "Test content"
        mock_loader_instance = Mock()
        mock_loader_instance.load.return_value = [mock_doc]
        mock_loader.return_value = mock_loader_instance

        result = process_html("test_folder", split_text=False)

        assert len(result) == 1
        assert result[0].metadata["url"] == "https://example.com"
        assert result[0].metadata["source"] == "test.html"

    @patch("src.tools.process_html.glob.glob")
    @patch("src.tools.process_html.UnstructuredHTMLLoader")
    @patch(
        "builtins.open",
        new_callable=mock_open,
        read_data='{"test.html": "https://example.com"}',
    )
    @patch("src.tools.process_html.os.path.exists")
    @patch("src.tools.process_html.os.listdir")
    @patch("src.tools.process_html.text_splitter.split_documents")
    @patch("src.tools.process_html.chunk_documents")
    def test_process_html_with_splitting(
        self,
        mock_chunk,
        mock_split,
        mock_listdir,
        mock_exists,
        mock_file,
        mock_loader,
        mock_glob,
    ):
        """Test processing HTML with text splitting."""
        # Setup mocks
        mock_exists.return_value = True
        mock_listdir.return_value = ["test.html"]
        mock_glob.return_value = ["./test.html"]

        mock_doc = Mock()
        mock_doc.metadata = {"source": "test.html"}
        mock_doc.page_content = "Test content"
        mock_loader_instance = Mock()
        mock_loader_instance.load.return_value = [mock_doc]
        mock_loader.return_value = mock_loader_instance

        mock_split.return_value = [mock_doc]
        mock_chunk.return_value = [mock_doc]

        result = process_html("test_folder", split_text=True, chunk_size=500)

        assert len(result) == 1
        mock_split.assert_called_once()
        mock_chunk.assert_called_once_with(500, [mock_doc])

    @patch("src.tools.process_html.glob.glob")
    @patch("src.tools.process_html.UnstructuredHTMLLoader")
    @patch("builtins.open", new_callable=mock_open, read_data="{}")
    @patch("src.tools.process_html.os.path.exists")
    @patch("src.tools.process_html.os.listdir")
    def test_process_html_missing_source_in_dict(
        self, mock_listdir, mock_exists, mock_file, mock_loader, mock_glob
    ):
        """Test processing HTML when source not found in source_list.json."""
        # Setup mocks
        mock_exists.return_value = True
        mock_listdir.return_value = ["test.html"]
        mock_glob.return_value = ["./test.html"]

        mock_doc = Mock()
        mock_doc.metadata = {"source": "test.html"}
        mock_doc.page_content = "Test content"
        mock_loader_instance = Mock()
        mock_loader_instance.load.return_value = [mock_doc]
        mock_loader.return_value = mock_loader_instance

        result = process_html("test_folder", split_text=False)

        assert len(result) == 1
        assert result[0].metadata["url"] == ""
        assert result[0].metadata["source"] == "test.html"

    def test_process_html_split_without_chunk_size_raises_error(self):
        """Test that splitting without chunk_size raises ValueError."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create a dummy HTML file
            html_file = Path(temp_dir) / "test.html"
            html_file.write_text("<html><body>Test</body></html>")

            with patch(
                "builtins.open",
                mock_open(read_data='{"test.html": "https://example.com"}'),
            ):
                with patch(
                    "src.tools.process_html.UnstructuredHTMLLoader"
                ) as mock_loader:
                    mock_doc = Mock()
                    mock_doc.metadata = {"source": "test.html"}
                    mock_loader_instance = Mock()
                    mock_loader_instance.load.return_value = [mock_doc]
                    mock_loader.return_value = mock_loader_instance

                    with pytest.raises(ValueError, match="Chunk size not set"):
                        process_html(temp_dir, split_text=True, chunk_size=None)

    @patch("src.tools.process_html.glob.glob")
    @patch("src.tools.process_html.UnstructuredHTMLLoader")
    @patch(
        "builtins.open",
        new_callable=mock_open,
        read_data='{"file1.html": "https://example1.com", "file2.html": "https://example2.com"}',
    )
    @patch("src.tools.process_html.os.path.exists")
    @patch("src.tools.process_html.os.listdir")
    def test_process_html_multiple_files(
        self, mock_listdir, mock_exists, mock_file, mock_loader, mock_glob
    ):
        """Test processing multiple HTML files."""
        # Setup mocks
        mock_exists.return_value = True
        mock_listdir.return_value = ["file1.html", "file2.html"]
        mock_glob.return_value = ["./file1.html", "./file2.html"]

        mock_doc1 = Mock()
        mock_doc1.metadata = {"source": "file1.html"}
        mock_doc1.page_content = "Content 1"

        mock_doc2 = Mock()
        mock_doc2.metadata = {"source": "file2.html"}
        mock_doc2.page_content = "Content 2"

        def loader_side_effect(file_path):
            mock_loader_instance = Mock()
            if "file1.html" in file_path:
                mock_loader_instance.load.return_value = [mock_doc1]
            else:
                mock_loader_instance.load.return_value = [mock_doc2]
            return mock_loader_instance

        mock_loader.side_effect = loader_side_effect

        result = process_html("test_folder", split_text=False)

        assert len(result) == 2
        sources = [doc.metadata["source"] for doc in result]
        assert "file1.html" in sources
        assert "file2.html" in sources

    @patch("src.tools.process_html.logging")
    def test_process_html_logs_error_for_empty_folder(self, mock_logging):
        """Test that error is logged for empty folder."""
        with tempfile.TemporaryDirectory() as temp_dir:
            result = process_html(temp_dir)

            assert result == []
            mock_logging.error.assert_called_once()

    @patch("src.tools.process_html.logging")
    @patch("src.tools.process_html.glob.glob")
    @patch("src.tools.process_html.UnstructuredHTMLLoader")
    @patch("builtins.open", new_callable=mock_open, read_data="{}")
    @patch("src.tools.process_html.os.path.exists")
    @patch("src.tools.process_html.os.listdir")
    def test_process_html_logs_warning_for_missing_source(
        self, mock_listdir, mock_exists, mock_file, mock_loader, mock_glob, mock_logging
    ):
        """Test that warning is logged when source not found in JSON."""
        # Setup mocks
        mock_exists.return_value = True
        mock_listdir.return_value = ["test.html"]
        mock_glob.return_value = ["./test.html"]

        mock_doc = Mock()
        mock_doc.metadata = {"source": "test.html"}
        mock_loader_instance = Mock()
        mock_loader_instance.load.return_value = [mock_doc]
        mock_loader.return_value = mock_loader_instance

        process_html("test_folder", split_text=False)

        mock_logging.warning.assert_called_once()

    @pytest.mark.unit
    def test_process_html_metadata_transformation(self):
        """Test that metadata is properly transformed."""
        with patch("src.tools.process_html.glob.glob") as mock_glob:
            with patch("src.tools.process_html.UnstructuredHTMLLoader") as mock_loader:
                with patch(
                    "builtins.open",
                    mock_open(read_data='{"test.html": "https://example.com"}'),
                ):
                    with patch(
                        "src.tools.process_html.os.path.exists", return_value=True
                    ):
                        with patch(
                            "src.tools.process_html.os.listdir",
                            return_value=["test.html"],
                        ):
                            mock_glob.return_value = ["./nested/path/test.html"]

                            mock_doc = Mock()
                            mock_doc.metadata = {
                                "source": "original_source",
                                "other_key": "other_value",
                            }
                            mock_doc.page_content = "Test content"
                            mock_loader_instance = Mock()
                            mock_loader_instance.load.return_value = [mock_doc]
                            mock_loader.return_value = mock_loader_instance

                            result = process_html("test_folder", split_text=False)

                            assert len(result) == 1
                            # Check that metadata was replaced
                            assert (
                                "nested/path/test.html" in result[0].metadata["source"]
                            )
                            # URL will be empty since source not found in our mock JSON
                            assert result[0].metadata["url"] == ""
                            # Original metadata should be gone
                            assert "other_key" not in result[0].metadata

    @pytest.mark.integration
    def test_process_html_real_file_structure(self):
        """Test with a realistic file structure."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create nested directory structure
            nested_dir = Path(temp_dir) / "docs" / "html"
            nested_dir.mkdir(parents=True)

            # Create HTML file
            html_file = nested_dir / "test.html"
            html_file.write_text(
                "<html><head><title>Test</title></head><body><h1>Test Content</h1></body></html>"
            )

            # Mock the source_list.json
            with patch(
                "builtins.open",
                mock_open(read_data='{"docs/html/test.html": "https://example.com"}'),
            ):
                with patch(
                    "src.tools.process_html.UnstructuredHTMLLoader"
                ) as mock_loader:
                    mock_doc = Mock()
                    mock_doc.metadata = {"source": "test.html"}
                    mock_doc.page_content = "Test Content"
                    mock_loader_instance = Mock()
                    mock_loader_instance.load.return_value = [mock_doc]
                    mock_loader.return_value = mock_loader_instance

                    result = process_html(str(temp_dir), split_text=False)

                    assert len(result) == 1
                    # The source won't be found in our mock JSON, so URL will be empty
                    assert result[0].metadata["url"] == ""
