import pytest
from unittest.mock import patch

from src.tools.process_md import md_to_text


class TestMdToText:
    """Test suite for process_md utility functions."""

    def test_md_to_text_basic(self):
        """Test basic markdown to text conversion."""
        md_content = "# Hello World\n\nThis is **bold** text."

        result = md_to_text(md_content)

        assert "Hello World" in result
        assert "This is bold text." in result
        # Should not contain markdown syntax
        assert "#" not in result
        assert "**" not in result

    def test_md_to_text_with_links(self):
        """Test markdown with links."""
        md_content = (
            "Check out [OpenROAD](https://openroad.readthedocs.io/) for more info."
        )

        result = md_to_text(md_content)

        assert "Check out OpenROAD for more info." in result
        # Should not contain markdown link syntax
        assert "[" not in result
        assert "]" not in result
        assert "(" not in result or ")" not in result

    def test_md_to_text_with_code_blocks(self):
        """Test markdown with code blocks."""
        md_content = """# Installation

Run this command:

```bash
make install
```

Then proceed."""

        result = md_to_text(md_content)

        assert "Installation" in result
        assert "Run this command:" in result
        assert "make install" in result
        assert "Then proceed." in result

    def test_md_to_text_with_lists(self):
        """Test markdown with lists."""
        md_content = """
        # Features

        - Feature 1
        - Feature 2
        - Feature 3

        1. Step 1
        2. Step 2
        """

        result = md_to_text(md_content)

        assert "Features" in result
        assert "Feature 1" in result
        assert "Feature 2" in result
        assert "Feature 3" in result
        assert "Step 1" in result
        assert "Step 2" in result

    def test_md_to_text_with_tables(self):
        """Test markdown with tables."""
        md_content = """
        | Command | Description |
        |---------|-------------|
        | make test | Run tests |
        | make build | Build project |
        """

        result = md_to_text(md_content)

        assert "Command" in result
        assert "Description" in result
        assert "make test" in result
        assert "Run tests" in result
        assert "make build" in result
        assert "Build project" in result

    def test_md_to_text_empty_content(self):
        """Test with empty markdown content."""
        md_content = ""

        result = md_to_text(md_content)

        assert result == ""

    def test_md_to_text_whitespace_only(self):
        """Test with whitespace-only content."""
        md_content = "   \n\n   \t  \n"

        result = md_to_text(md_content)

        # Should return minimal whitespace
        assert result.strip() == ""

    def test_md_to_text_complex_formatting(self):
        """Test with complex markdown formatting."""
        md_content = """# OpenROAD Flow

The **OpenROAD** flow consists of several stages:

## Synthesis

The synthesis stage uses *Yosys* to convert RTL to netlist.

### Configuration

Configure with:

```tcl
set_design_name "my_design"
```

> **Note**: This is important!

For more details, see [documentation](https://docs.example.com)."""

        result = md_to_text(md_content)

        # Check content is preserved
        assert "OpenROAD Flow" in result
        assert "OpenROAD" in result
        assert "Synthesis" in result
        assert "Yosys" in result
        assert "Configuration" in result
        assert "set_design_name" in result
        assert "Note" in result
        assert "important" in result
        assert "documentation" in result

    @pytest.mark.unit
    def test_md_to_text_html_entities(self):
        """Test markdown that generates HTML entities."""
        md_content = "Use `<command>` and `&parameter`"

        result = md_to_text(md_content)

        assert "<command>" in result
        assert "&parameter" in result

    @pytest.mark.unit
    def test_md_to_text_special_characters(self):
        """Test with special characters in markdown."""
        md_content = "# Title with émojis 🚀 and spëcial chars"

        result = md_to_text(md_content)

        assert "Title with émojis 🚀 and spëcial chars" in result
        assert "#" not in result


class TestLoadDocs:
    """Test suite for load_docs function."""

    @patch("src.tools.process_md.glob.glob")
    @patch("builtins.open", create=True)
    @patch("src.tools.process_md.md_to_text")
    def test_load_docs_single_file(self, mock_md_to_text, mock_open, mock_glob):
        """Test loading a single markdown file."""
        mock_glob.return_value = ["./test.md"]
        mock_open.return_value.__enter__.return_value.read.return_value = (
            "# Test Content"
        )
        mock_md_to_text.return_value = "Test Content"

        from src.tools.process_md import load_docs

        result = load_docs("test_folder")

        assert len(result) == 1
        assert result[0].page_content == "Test Content"
        assert result[0].metadata["source"] == "test.md"

    @patch("src.tools.process_md.glob.glob")
    @patch("builtins.open", create=True)
    @patch("src.tools.process_md.md_to_text")
    def test_load_docs_multiple_files(self, mock_md_to_text, mock_open, mock_glob):
        """Test loading multiple markdown files."""
        mock_glob.return_value = ["./file1.md", "./file2.md"]
        mock_open.return_value.__enter__.return_value.read.side_effect = [
            "# Content 1",
            "# Content 2",
        ]
        mock_md_to_text.side_effect = ["Content 1", "Content 2"]

        from src.tools.process_md import load_docs

        result = load_docs("test_folder")

        assert len(result) == 2
        assert result[0].page_content == "Content 1"
        assert result[0].metadata["source"] == "file1.md"
        assert result[1].page_content == "Content 2"
        assert result[1].metadata["source"] == "file2.md"

    @patch("src.tools.process_md.glob.glob")
    def test_load_docs_no_files(self, mock_glob):
        """Test loading from folder with no markdown files."""
        mock_glob.return_value = []

        from src.tools.process_md import load_docs

        result = load_docs("empty_folder")

        assert result == []


class TestProcessMd:
    """Test suite for process_md function."""

    @patch("src.tools.process_md.os.path.exists")
    @patch("src.tools.process_md.os.listdir")
    def test_process_md_nonexistent_folder(self, mock_listdir, mock_exists):
        """Test processing nonexistent folder."""
        mock_exists.return_value = False

        from src.tools.process_md import process_md

        result = process_md("nonexistent_folder")

        assert result == []

    @patch("src.tools.process_md.os.path.exists")
    @patch("src.tools.process_md.os.listdir")
    def test_process_md_empty_folder(self, mock_listdir, mock_exists):
        """Test processing empty folder."""
        mock_exists.return_value = True
        mock_listdir.return_value = []

        from src.tools.process_md import process_md

        result = process_md("empty_folder")

        assert result == []

    @patch("src.tools.process_md.os.path.exists")
    @patch("src.tools.process_md.os.listdir")
    @patch("src.tools.process_md.load_docs")
    @patch("builtins.open", create=True)
    def test_process_md_without_splitting(
        self, mock_open, mock_load_docs, mock_listdir, mock_exists
    ):
        """Test processing markdown files without text splitting."""
        mock_exists.return_value = True
        mock_listdir.return_value = ["file.md"]
        mock_open.return_value.__enter__.return_value.read.return_value = (
            '{"test.md": "https://example.com"}'
        )

        from langchain.docstore.document import Document

        mock_docs = [
            Document(page_content="Test content", metadata={"source": "test.md"})
        ]
        mock_load_docs.return_value = mock_docs

        from src.tools.process_md import process_md

        result = process_md("test_folder", split_text=False)

        assert len(result) == 1
        assert result[0].metadata["url"] == "https://example.com"
        assert result[0].metadata["source"] == "test.md"

    @patch("src.tools.process_md.os.path.exists")
    @patch("src.tools.process_md.os.listdir")
    @patch("src.tools.process_md.load_docs")
    @patch("src.tools.process_md.text_splitter.split_documents")
    @patch("src.tools.process_md.chunk_documents")
    @patch("builtins.open", create=True)
    def test_process_md_with_splitting(
        self,
        mock_open,
        mock_chunk,
        mock_split,
        mock_load_docs,
        mock_listdir,
        mock_exists,
    ):
        """Test processing markdown files with text splitting."""
        mock_exists.return_value = True
        mock_listdir.return_value = ["file.md"]
        mock_open.return_value.__enter__.return_value.read.return_value = (
            '{"test.md": "https://example.com"}'
        )

        from langchain.docstore.document import Document

        mock_doc = Document(page_content="Test content", metadata={"source": "test.md"})
        mock_load_docs.return_value = [mock_doc]
        mock_split.return_value = [mock_doc]
        mock_chunk.return_value = [mock_doc]

        from src.tools.process_md import process_md

        result = process_md("test_folder", split_text=True, chunk_size=500)

        assert len(result) == 1
        mock_split.assert_called_once()
        mock_chunk.assert_called_once_with(500, [mock_doc])

    @patch("src.tools.process_md.os.path.exists")
    @patch("src.tools.process_md.os.listdir")
    def test_process_md_split_without_chunk_size_raises_error(
        self, mock_listdir, mock_exists
    ):
        """Test that splitting without chunk_size raises ValueError."""
        mock_exists.return_value = True
        mock_listdir.return_value = ["file.md"]

        from src.tools.process_md import process_md

        with pytest.raises(ValueError, match="Chunk size not set"):
            process_md("test_folder", split_text=True, chunk_size=None)

    @patch("src.tools.process_md.os.path.exists")
    @patch("src.tools.process_md.os.listdir")
    @patch("src.tools.process_md.load_docs")
    @patch("builtins.open", create=True)
    def test_process_md_missing_source_in_dict(
        self, mock_open, mock_load_docs, mock_listdir, mock_exists
    ):
        """Test processing when source not found in source_list.json."""
        mock_exists.return_value = True
        mock_listdir.return_value = ["file.md"]
        mock_open.return_value.__enter__.return_value.read.return_value = (
            "{}"  # Empty JSON
        )

        from langchain.docstore.document import Document

        mock_docs = [
            Document(page_content="Test content", metadata={"source": "missing.md"})
        ]
        mock_load_docs.return_value = mock_docs

        from src.tools.process_md import process_md

        result = process_md("test_folder", split_text=False)

        assert len(result) == 1
        assert result[0].metadata["url"] == ""
        assert result[0].metadata["source"] == "missing.md"

    @patch("src.tools.process_md.logging")
    @patch("src.tools.process_md.os.path.exists")
    @patch("src.tools.process_md.os.listdir")
    def test_process_md_logs_error_for_empty_folder(
        self, mock_listdir, mock_exists, mock_logging
    ):
        """Test that error is logged for empty folder."""
        mock_exists.return_value = True
        mock_listdir.return_value = []

        from src.tools.process_md import process_md

        result = process_md("empty_folder")

        assert result == []
        mock_logging.error.assert_called_once()

    @patch("src.tools.process_md.logging")
    @patch("src.tools.process_md.os.path.exists")
    @patch("src.tools.process_md.os.listdir")
    @patch("src.tools.process_md.load_docs")
    @patch("builtins.open", create=True)
    def test_process_md_logs_warning_for_missing_source(
        self, mock_open, mock_load_docs, mock_listdir, mock_exists, mock_logging
    ):
        """Test that warning is logged when source not found in JSON."""
        mock_exists.return_value = True
        mock_listdir.return_value = ["file.md"]
        mock_open.return_value.__enter__.return_value.read.return_value = "{}"

        from langchain.docstore.document import Document

        mock_docs = [
            Document(page_content="Test content", metadata={"source": "missing.md"})
        ]
        mock_load_docs.return_value = mock_docs

        from src.tools.process_md import process_md

        process_md("test_folder", split_text=False)

        mock_logging.warning.assert_called_once()

    @pytest.mark.integration
    @patch("src.tools.process_md.os.path.exists")
    @patch("src.tools.process_md.os.listdir")
    @patch("src.tools.process_md.load_docs")
    @patch("builtins.open")
    def test_process_md_realistic_workflow(
        self, mock_open, mock_load_docs, mock_listdir, mock_exists
    ):
        """Test process_md with realistic workflow."""
        mock_exists.return_value = True
        mock_listdir.return_value = ["installation.md", "usage.md"]
        mock_open.return_value.__enter__.return_value.read.return_value = '{"installation.md": "https://docs.example.com/install", "usage.md": "https://docs.example.com/usage"}'

        from langchain.docstore.document import Document

        mock_docs = [
            Document(
                page_content="Installation content",
                metadata={"source": "installation.md"},
            ),
            Document(page_content="Usage content", metadata={"source": "usage.md"}),
        ]
        mock_load_docs.return_value = mock_docs

        from src.tools.process_md import process_md

        result = process_md("test_folder", split_text=False)

        assert len(result) == 2
        sources = [doc.metadata["source"] for doc in result]
        assert "installation.md" in sources
        assert "usage.md" in sources
