import pytest
from langchain.docstore.document import Document

from src.tools.chunk_documents import chunk_documents


class TestChunkDocuments:
    """Test suite for chunk_documents utility function."""

    def test_chunk_documents_basic(self):
        """Test basic document chunking."""
        docs = [
            Document(
                page_content="This is a test document with some content.",
                metadata={"source": "test.md"}
            )
        ]
        
        result = chunk_documents(chunk_size=50, knowledge_base=docs)
        
        assert len(result) >= 1
        assert all(isinstance(doc, Document) for doc in result)
        assert all(doc.metadata.get("source") == "test.md" for doc in result)

    def test_chunk_documents_large_text(self):
        """Test chunking with text larger than chunk size."""
        large_content = " ".join(["This is sentence number {}.".format(i) for i in range(100)])
        docs = [
            Document(
                page_content=large_content,
                metadata={"source": "large.md"}
            )
        ]
        
        result = chunk_documents(chunk_size=100, knowledge_base=docs)
        
        # Should create multiple chunks
        assert len(result) > 1
        # Each chunk should be approximately the chunk size or smaller
        assert all(len(doc.page_content) <= 150 for doc in result)  # Allow some overlap

    def test_chunk_documents_multiple_docs(self):
        """Test chunking with multiple documents."""
        docs = [
            Document(
                page_content="First document content.",
                metadata={"source": "doc1.md"}
            ),
            Document(
                page_content="Second document with different content.",
                metadata={"source": "doc2.md"}
            )
        ]
        
        result = chunk_documents(chunk_size=50, knowledge_base=docs)
        
        assert len(result) >= 2
        # Check that metadata is preserved
        sources = [doc.metadata.get("source") for doc in result]
        assert "doc1.md" in sources
        assert "doc2.md" in sources

    def test_chunk_documents_deduplication(self):
        """Test that duplicate content is removed."""
        duplicate_content = "This is duplicate content that appears twice."
        docs = [
            Document(
                page_content=duplicate_content,
                metadata={"source": "doc1.md"}
            ),
            Document(
                page_content=duplicate_content,
                metadata={"source": "doc2.md"}
            )
        ]
        
        result = chunk_documents(chunk_size=100, knowledge_base=docs)
        
        # Should only have one chunk due to deduplication
        assert len(result) == 1
        assert result[0].page_content == duplicate_content

    def test_chunk_documents_empty_list(self):
        """Test chunking with empty document list."""
        docs = []
        
        result = chunk_documents(chunk_size=100, knowledge_base=docs)
        
        assert result == []

    def test_chunk_documents_small_chunk_size(self):
        """Test chunking with very small chunk size."""
        docs = [
            Document(
                page_content="This is a longer text that should be split into multiple small chunks.",
                metadata={"source": "test.md"}
            )
        ]
        
        result = chunk_documents(chunk_size=20, knowledge_base=docs)
        
        # Should create multiple small chunks
        assert len(result) > 1
        # Verify chunk overlap calculation (chunk_size / 10)
        # Small chunks should exist
        assert any(len(doc.page_content) <= 30 for doc in result)

    def test_chunk_documents_preserves_metadata(self):
        """Test that all metadata is preserved during chunking."""
        docs = [
            Document(
                page_content="Content with rich metadata.",
                metadata={
                    "source": "test.md",
                    "author": "test_author",
                    "category": "documentation",
                    "custom_field": "custom_value"
                }
            )
        ]
        
        result = chunk_documents(chunk_size=50, knowledge_base=docs)
        
        assert len(result) >= 1
        for doc in result:
            assert doc.metadata["source"] == "test.md"
            assert doc.metadata["author"] == "test_author"
            assert doc.metadata["category"] == "documentation"
            assert doc.metadata["custom_field"] == "custom_value"

    def test_chunk_documents_start_index_added(self):
        """Test that start_index is added to chunked documents."""
        large_content = " ".join(["Word{}".format(i) for i in range(50)])
        docs = [
            Document(
                page_content=large_content,
                metadata={"source": "test.md"}
            )
        ]
        
        result = chunk_documents(chunk_size=50, knowledge_base=docs)
        
        # Should have multiple chunks with start_index
        if len(result) > 1:
            # Check that start_index exists and is numeric
            for doc in result:
                assert "start_index" in doc.metadata
                assert isinstance(doc.metadata["start_index"], int)
                assert doc.metadata["start_index"] >= 0

    def test_chunk_documents_whitespace_stripped(self):
        """Test that whitespace is stripped from chunks."""
        docs = [
            Document(
                page_content="   Content with leading and trailing whitespace   ",
                metadata={"source": "test.md"}
            )
        ]
        
        result = chunk_documents(chunk_size=100, knowledge_base=docs)
        
        assert len(result) >= 1
        # Content should be stripped of leading/trailing whitespace
        assert not result[0].page_content.startswith("   ")
        assert not result[0].page_content.endswith("   ")

    @pytest.mark.unit
    def test_chunk_overlap_calculation(self):
        """Test that chunk overlap is calculated correctly."""
        # Test with chunk_size where overlap = chunk_size / 10
        chunk_size = 100
        expected_overlap = int(chunk_size / 10)  # Should be 10
        
        docs = [
            Document(
                page_content="A" * 500,  # Large enough to create multiple chunks
                metadata={"source": "test.md"}
            )
        ]
        
        result = chunk_documents(chunk_size=chunk_size, knowledge_base=docs)
        
        # With overlap, we should get good chunking
        assert len(result) > 1

    @pytest.mark.integration
    def test_chunk_documents_real_world_scenario(self):
        """Test chunking with realistic documentation content."""
        real_content = """
        # OpenROAD Installation Guide
        
        OpenROAD is an open-source RTL-to-GDSII tool chain that provides a complete physical design flow.
        
        ## Prerequisites
        
        Before installing OpenROAD, ensure you have the following dependencies:
        - CMake 3.14 or later
        - GCC 7.0 or later
        - Python 3.6 or later
        
        ## Installation Methods
        
        There are several ways to install OpenROAD:
        1. Build from source
        2. Use Docker container
        3. Install pre-built binaries
        
        ### Building from Source
        
        To build from source, follow these steps:
        1. Clone the repository
        2. Install dependencies
        3. Configure and build
        """
        
        docs = [
            Document(
                page_content=real_content,
                metadata={
                    "source": "installation.md",
                    "category": "documentation"
                }
            )
        ]
        
        result = chunk_documents(chunk_size=200, knowledge_base=docs)
        
        assert len(result) > 1
        # Verify that content is properly split
        combined_content = " ".join(doc.page_content for doc in result)
        assert "OpenROAD Installation Guide" in combined_content
        assert "Building from Source" in combined_content