import pytest
from langchain.docstore.document import Document

from src.tools.format_docs import format_docs, CHUNK_SEPARATOR


class TestFormatDocs:
    """Test suite for format_docs utility function."""

    def test_format_docs_basic(self):
        """Test basic document formatting."""
        docs = [
            Document(
                page_content="Content 1",
                metadata={"source": "test1.md"}
            ),
            Document(
                page_content="Content 2", 
                metadata={"source": "test2.md"}
            )
        ]
        
        doc_output, doc_srcs, doc_urls, doc_texts = format_docs(docs)
        
        expected_output = f"Content 1{CHUNK_SEPARATOR}Content 2"
        assert doc_output == expected_output
        assert doc_srcs == ["test1.md", "test2.md"]
        assert doc_urls == []
        assert doc_texts == ["Content 1", "Content 2"]

    def test_format_docs_with_man1_source(self):
        """Test formatting with man1 source (command documentation)."""
        docs = [
            Document(
                page_content="Command documentation",
                metadata={"source": "manpages/man1/openroad.md"}
            )
        ]
        
        doc_output, doc_srcs, doc_urls, doc_texts = format_docs(docs)
        
        expected_text = "Command Name: openroad\n\nCommand documentation"
        assert doc_texts[0] == expected_text
        assert doc_srcs == ["manpages/man1/openroad.md"]

    def test_format_docs_with_man2_source(self):
        """Test formatting with man2 source (command documentation)."""
        docs = [
            Document(
                page_content="Tool documentation",
                metadata={"source": "manpages/man2/place_pins.md"}
            )
        ]
        
        doc_output, doc_srcs, doc_urls, doc_texts = format_docs(docs)
        
        expected_text = "Command Name: place_pins\n\nTool documentation"
        assert doc_texts[0] == expected_text
        assert doc_srcs == ["manpages/man2/place_pins.md"]

    def test_format_docs_with_gh_discussions_source(self):
        """Test formatting with GitHub discussions source."""
        docs = [
            Document(
                page_content="Discussion content",
                metadata={"source": "gh_discussions/Bug/1234.md"}
            )
        ]
        
        doc_output, doc_srcs, doc_urls, doc_texts = format_docs(docs)
        
        # Should include the gh_discussion_prompt_template
        assert "discussion content" in doc_texts[0].lower()
        assert doc_srcs == ["gh_discussions/Bug/1234.md"]

    def test_format_docs_with_urls(self):
        """Test formatting with URL metadata."""
        docs = [
            Document(
                page_content="Web content",
                metadata={
                    "source": "web.md",
                    "url": "https://example.com"
                }
            ),
            Document(
                page_content="More web content",
                metadata={
                    "source": "web2.md", 
                    "url": "https://example2.com"
                }
            )
        ]
        
        doc_output, doc_srcs, doc_urls, doc_texts = format_docs(docs)
        
        assert doc_urls == ["https://example.com", "https://example2.com"]
        assert doc_srcs == ["web.md", "web2.md"]

    def test_format_docs_mixed_sources(self):
        """Test formatting with mixed source types."""
        docs = [
            Document(
                page_content="Regular content",
                metadata={"source": "regular.md"}
            ),
            Document(
                page_content="Command content",
                metadata={"source": "manpages/man1/command.md"}
            ),
            Document(
                page_content="Discussion content",
                metadata={"source": "gh_discussions/Query/5678.md"}
            )
        ]
        
        doc_output, doc_srcs, doc_urls, doc_texts = format_docs(docs)
        
        assert len(doc_texts) == 3
        assert doc_texts[0] == "Regular content"
        assert "Command Name: command" in doc_texts[1]
        assert "Discussion content" in doc_texts[2]

    def test_format_docs_empty_list(self):
        """Test formatting with empty document list."""
        docs = []
        
        doc_output, doc_srcs, doc_urls, doc_texts = format_docs(docs)
        
        assert doc_output == ""
        assert doc_srcs == []
        assert doc_urls == []
        assert doc_texts == []

    def test_format_docs_no_source_metadata(self):
        """Test formatting with documents missing source metadata."""
        docs = [
            Document(
                page_content="Content without source",
                metadata={"other": "metadata"}
            )
        ]
        
        doc_output, doc_srcs, doc_urls, doc_texts = format_docs(docs)
        
        assert doc_output == ""
        assert doc_srcs == []
        assert doc_urls == []
        assert doc_texts == []

    def test_format_docs_partial_metadata(self):
        """Test formatting with some docs having metadata, others not."""
        docs = [
            Document(
                page_content="With source",
                metadata={"source": "test.md"}
            ),
            Document(
                page_content="Without source",
                metadata={"other": "data"}
            ),
            Document(
                page_content="With source and URL",
                metadata={
                    "source": "test2.md",
                    "url": "https://example.com"
                }
            )
        ]
        
        doc_output, doc_srcs, doc_urls, doc_texts = format_docs(docs)
        
        expected_output = f"With source{CHUNK_SEPARATOR}With source and URL"
        assert doc_output == expected_output
        assert doc_srcs == ["test.md", "test2.md"]
        assert doc_urls == ["https://example.com"]
        assert doc_texts == ["With source", "With source and URL"]

    @pytest.mark.unit
    def test_chunk_separator_constant(self):
        """Test that CHUNK_SEPARATOR constant is properly defined."""
        assert CHUNK_SEPARATOR == "\n\n -------------------------- \n\n"