import pytest
import os
import tempfile
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path

from langchain_community.vectorstores.utils import DistanceStrategy
from langchain.docstore.document import Document

from src.vectorstores.faiss import FAISSVectorDatabase


class TestFAISSVectorDatabase:
    """Test suite for FAISSVectorDatabase class."""

    def test_init_with_huggingface_embeddings(self):
        """Test initialization with HuggingFace embeddings."""
        with patch('src.vectorstores.faiss.HuggingFaceEmbeddings') as mock_hf:
            mock_hf.return_value = Mock()
            
            db = FAISSVectorDatabase(
                embeddings_type="HF",
                embeddings_model_name="sentence-transformers/all-MiniLM-L6-v2"
            )
            
            assert db.embeddings_model_name == "sentence-transformers/all-MiniLM-L6-v2"
            assert db.distance_strategy == DistanceStrategy.COSINE
            assert db.debug is False
            assert db.processed_docs == []
            assert db.faiss_db is None
            
            mock_hf.assert_called_once()

    def test_init_with_google_genai_embeddings(self):
        """Test initialization with Google GenAI embeddings."""
        with patch('src.vectorstores.faiss.GoogleGenerativeAIEmbeddings') as mock_genai:
            mock_genai.return_value = Mock()
            
            db = FAISSVectorDatabase(
                embeddings_type="GOOGLE_GENAI",
                embeddings_model_name="models/embedding-001"
            )
            
            assert db.embeddings_model_name == "models/embedding-001"
            mock_genai.assert_called_once_with(
                model="models/embedding-001",
                task_type="retrieval_document"
            )

    def test_init_with_google_vertexai_embeddings(self):
        """Test initialization with Google VertexAI embeddings."""
        with patch('src.vectorstores.faiss.VertexAIEmbeddings') as mock_vertex:
            mock_vertex.return_value = Mock()
            
            db = FAISSVectorDatabase(
                embeddings_type="GOOGLE_VERTEXAI",
                embeddings_model_name="textembedding-gecko@001"
            )
            
            assert db.embeddings_model_name == "textembedding-gecko@001"
            mock_vertex.assert_called_once_with(
                model_name="textembedding-gecko@001"
            )

    def test_init_with_invalid_embeddings_type(self):
        """Test initialization with invalid embeddings type raises error."""
        with pytest.raises(ValueError, match="Invalid embdeddings type specified"):
            FAISSVectorDatabase(
                embeddings_type="INVALID",
                embeddings_model_name="test-model"
            )

    def test_init_with_cuda_enabled(self):
        """Test initialization with CUDA enabled."""
        with patch('src.vectorstores.faiss.HuggingFaceEmbeddings') as mock_hf:
            mock_hf.return_value = Mock()
            
            db = FAISSVectorDatabase(
                embeddings_type="HF",
                embeddings_model_name="test-model",
                use_cuda=True
            )
            
            mock_hf.assert_called_once()
            call_args = mock_hf.call_args
            assert call_args[1]['model_kwargs']['device'] == 'cuda'

    def test_init_with_custom_distance_strategy(self):
        """Test initialization with custom distance strategy."""
        with patch('src.vectorstores.faiss.HuggingFaceEmbeddings') as mock_hf:
            mock_hf.return_value = Mock()
            
            db = FAISSVectorDatabase(
                embeddings_type="HF",
                embeddings_model_name="test-model",
                distance_strategy=DistanceStrategy.EUCLIDEAN_DISTANCE
            )
            
            assert db.distance_strategy == DistanceStrategy.EUCLIDEAN_DISTANCE

    @patch('src.vectorstores.faiss.FAISS')
    def test_add_to_db_creates_new_db(self, mock_faiss):
        """Test _add_to_db creates new FAISS database when none exists."""
        mock_faiss_instance = Mock()
        mock_faiss.from_documents.return_value = mock_faiss_instance
        
        with patch('src.vectorstores.faiss.HuggingFaceEmbeddings') as mock_hf:
            mock_hf.return_value = Mock()
            
            db = FAISSVectorDatabase(
                embeddings_type="HF",
                embeddings_model_name="test-model"
            )
            
            documents = [
                Document(page_content="Test content", metadata={"source": "test"})
            ]
            
            db._add_to_db(documents)
            
            assert db.faiss_db is mock_faiss_instance
            mock_faiss.from_documents.assert_called_once_with(
                documents=documents,
                embedding=db.embedding_model,
                distance_strategy=db.distance_strategy
            )

    @patch('src.vectorstores.faiss.FAISS')
    def test_add_to_db_adds_to_existing_db(self, mock_faiss):
        """Test _add_to_db adds to existing FAISS database."""
        mock_faiss_instance = Mock()
        mock_faiss.from_documents.return_value = mock_faiss_instance
        
        with patch('src.vectorstores.faiss.HuggingFaceEmbeddings') as mock_hf:
            mock_hf.return_value = Mock()
            
            db = FAISSVectorDatabase(
                embeddings_type="HF",
                embeddings_model_name="test-model"
            )
            
            # Create initial database
            documents1 = [
                Document(page_content="Test content 1", metadata={"source": "test1"})
            ]
            db._add_to_db(documents1)
            
            # Add more documents
            documents2 = [
                Document(page_content="Test content 2", metadata={"source": "test2"})
            ]
            db._add_to_db(documents2)
            
            # Should add to existing database
            db.faiss_db.add_documents.assert_called_once_with(documents2)

    @patch('src.vectorstores.faiss.process_md')
    def test_add_md_docs_success(self, mock_process_md):
        """Test successful addition of markdown documents."""
        mock_documents = [
            Document(page_content="Test MD content", metadata={"source": "test.md"})
        ]
        mock_process_md.return_value = mock_documents
        
        with patch('src.vectorstores.faiss.HuggingFaceEmbeddings') as mock_hf:
            with patch('src.vectorstores.faiss.FAISS') as mock_faiss:
                mock_hf.return_value = Mock()
                mock_faiss.from_documents.return_value = Mock()
                
                db = FAISSVectorDatabase(
                    embeddings_type="HF",
                    embeddings_model_name="test-model"
                )
                
                result = db.add_md_docs(
                    folder_paths=["test_folder"],
                    chunk_size=500,
                    return_docs=True
                )
                
                assert result == mock_documents
                assert len(db.processed_docs) == 1
                mock_process_md.assert_called_once_with(
                    folder_path="test_folder",
                    chunk_size=500,
                    split_text=True
                )

    def test_add_md_docs_invalid_folder_paths(self):
        """Test add_md_docs with invalid folder_paths parameter."""
        with patch('src.vectorstores.faiss.HuggingFaceEmbeddings') as mock_hf:
            mock_hf.return_value = Mock()
            
            db = FAISSVectorDatabase(
                embeddings_type="HF",
                embeddings_model_name="test-model"
            )
            
            with pytest.raises(ValueError, match="folder_paths must be a list"):
                db.add_md_docs(folder_paths="not_a_list")

    def test_get_db_path(self):
        """Test get_db_path returns correct path."""
        with patch('src.vectorstores.faiss.HuggingFaceEmbeddings') as mock_hf:
            mock_hf.return_value = Mock()
            
            db = FAISSVectorDatabase(
                embeddings_type="HF",
                embeddings_model_name="test-model"
            )
            
            path = db.get_db_path()
            assert path.endswith("faiss_db")
            assert os.path.isabs(path)

    def test_save_db_without_documents_raises_error(self):
        """Test save_db raises error when no documents in database."""
        with patch('src.vectorstores.faiss.HuggingFaceEmbeddings') as mock_hf:
            mock_hf.return_value = Mock()
            
            db = FAISSVectorDatabase(
                embeddings_type="HF",
                embeddings_model_name="test-model"
            )
            
            with pytest.raises(ValueError, match="No documents in FAISS database"):
                db.save_db("test_db")

    @patch('src.vectorstores.faiss.FAISS')
    def test_save_db_success(self, mock_faiss):
        """Test successful database saving."""
        mock_faiss_instance = Mock()
        mock_faiss.from_documents.return_value = mock_faiss_instance
        
        with patch('src.vectorstores.faiss.HuggingFaceEmbeddings') as mock_hf:
            mock_hf.return_value = Mock()
            
            db = FAISSVectorDatabase(
                embeddings_type="HF",
                embeddings_model_name="test-model"
            )
            
            # Add some documents to create the database
            documents = [
                Document(page_content="Test content", metadata={"source": "test"})
            ]
            db._add_to_db(documents)
            
            with patch.object(db, 'get_db_path', return_value="/test/path"):
                db.save_db("test_db")
                
                mock_faiss_instance.save_local.assert_called_once_with("/test/path/test_db")

    @patch('src.vectorstores.faiss.FAISS')
    def test_load_db_success(self, mock_faiss):
        """Test successful database loading."""
        mock_faiss_instance = Mock()
        mock_faiss.load_local.return_value = mock_faiss_instance
        
        with patch('src.vectorstores.faiss.HuggingFaceEmbeddings') as mock_hf:
            mock_hf.return_value = Mock()
            
            db = FAISSVectorDatabase(
                embeddings_type="HF",
                embeddings_model_name="test-model"
            )
            
            with patch.object(db, 'get_db_path', return_value="/test/path"):
                db.load_db("test_db")
                
                assert db.faiss_db is mock_faiss_instance
                mock_faiss.load_local.assert_called_once_with(
                    "/test/path/test_db",
                    db.embedding_model,
                    allow_dangerous_deserialization=True
                )

    @patch('src.vectorstores.faiss.FAISS')
    def test_get_relevant_documents_success(self, mock_faiss):
        """Test successful retrieval of relevant documents."""
        mock_documents = [
            Mock(page_content="Document 1 content"),
            Mock(page_content="Document 2 content")
        ]
        
        mock_faiss_instance = Mock()
        mock_faiss_instance.similarity_search.return_value = mock_documents
        mock_faiss.from_documents.return_value = mock_faiss_instance
        
        with patch('src.vectorstores.faiss.HuggingFaceEmbeddings') as mock_hf:
            mock_hf.return_value = Mock()
            
            db = FAISSVectorDatabase(
                embeddings_type="HF",
                embeddings_model_name="test-model"
            )
            
            # Add documents to create database
            documents = [
                Document(page_content="Test content", metadata={"source": "test"})
            ]
            db._add_to_db(documents)
            
            result = db.get_relevant_documents("test query", k=2)
            
            assert "Document 1 content" in result
            assert "Document 2 content" in result
            mock_faiss_instance.similarity_search.assert_called_once_with(
                query="test query", k=2
            )

    def test_get_relevant_documents_no_database_raises_error(self):
        """Test get_relevant_documents raises error when no database exists."""
        with patch('src.vectorstores.faiss.HuggingFaceEmbeddings') as mock_hf:
            mock_hf.return_value = Mock()
            
            db = FAISSVectorDatabase(
                embeddings_type="HF",
                embeddings_model_name="test-model"
            )
            
            with pytest.raises(ValueError, match="No documents in FAISS database"):
                db.get_relevant_documents("test query")

    @pytest.mark.unit
    def test_faiss_db_property(self):
        """Test faiss_db property returns correct value."""
        with patch('src.vectorstores.faiss.HuggingFaceEmbeddings') as mock_hf:
            mock_hf.return_value = Mock()
            
            db = FAISSVectorDatabase(
                embeddings_type="HF",
                embeddings_model_name="test-model"
            )
            
            assert db.faiss_db is None
            
            # Set the private attribute
            mock_faiss_instance = Mock()
            db._faiss_db = mock_faiss_instance
            
            assert db.faiss_db is mock_faiss_instance

    @pytest.mark.integration
    def test_full_workflow_with_mock_data(self):
        """Test complete workflow with mocked data."""
        with patch('src.vectorstores.faiss.HuggingFaceEmbeddings') as mock_hf:
            with patch('src.vectorstores.faiss.FAISS') as mock_faiss:
                with patch('src.vectorstores.faiss.process_md') as mock_process_md:
                    mock_hf.return_value = Mock()
                    mock_faiss_instance = Mock()
                    mock_faiss.from_documents.return_value = mock_faiss_instance
                    
                    mock_documents = [
                        Document(page_content="Test content", metadata={"source": "test.md"})
                    ]
                    mock_process_md.return_value = mock_documents
                    
                    db = FAISSVectorDatabase(
                        embeddings_type="HF",
                        embeddings_model_name="test-model"
                    )
                    
                    # Add documents
                    result = db.add_md_docs(
                        folder_paths=["test_folder"],
                        return_docs=True
                    )
                    
                    # Verify documents were added
                    assert result == mock_documents
                    assert len(db.processed_docs) == 1
                    assert db.faiss_db is mock_faiss_instance

    @patch('src.vectorstores.faiss.process_md')
    def test_add_md_manpages_success(self, mock_process_md):
        """Test successful addition of markdown manpages."""
        mock_documents = [
            Document(page_content="Test manpage content", metadata={"source": "test.md"})
        ]
        mock_process_md.return_value = mock_documents
        
        with patch('src.vectorstores.faiss.HuggingFaceEmbeddings') as mock_hf:
            with patch('src.vectorstores.faiss.FAISS') as mock_faiss:
                mock_hf.return_value = Mock()
                mock_faiss.from_documents.return_value = Mock()
                
                db = FAISSVectorDatabase(
                    embeddings_type="HF",
                    embeddings_model_name="test-model"
                )
                
                result = db.add_md_manpages(
                    folder_paths=["test_folder"],
                    chunk_size=500,
                    return_docs=True
                )
                
                assert result == mock_documents
                assert len(db.processed_docs) == 1
                mock_process_md.assert_called_once_with(
                    folder_path="test_folder",
                    split_text=False,
                    chunk_size=500
                )

    def test_add_md_manpages_invalid_folder_paths(self):
        """Test add_md_manpages with invalid folder_paths parameter."""
        with patch('src.vectorstores.faiss.HuggingFaceEmbeddings') as mock_hf:
            mock_hf.return_value = Mock()
            
            db = FAISSVectorDatabase(
                embeddings_type="HF",
                embeddings_model_name="test-model"
            )
            
            with pytest.raises(ValueError, match="folder_paths must be a list"):
                db.add_md_manpages(folder_paths="not_a_list")

    @patch('src.vectorstores.faiss.process_html')
    def test_add_html_success(self, mock_process_html):
        """Test successful addition of HTML documents."""
        mock_documents = [
            Document(page_content="Test HTML content", metadata={"source": "test.html"})
        ]
        mock_process_html.return_value = mock_documents
        
        with patch('src.vectorstores.faiss.HuggingFaceEmbeddings') as mock_hf:
            with patch('src.vectorstores.faiss.FAISS') as mock_faiss:
                mock_hf.return_value = Mock()
                mock_faiss.from_documents.return_value = Mock()
                
                db = FAISSVectorDatabase(
                    embeddings_type="HF",
                    embeddings_model_name="test-model"
                )
                
                result = db.add_html(
                    folder_paths=["test_folder"],
                    chunk_size=500,
                    return_docs=True
                )
                
                assert result == mock_documents
                assert len(db.processed_docs) == 1
                mock_process_html.assert_called_once_with(
                    folder_path="test_folder",
                    split_text=True,
                    chunk_size=500
                )

    def test_add_html_invalid_folder_paths(self):
        """Test add_html with invalid folder_paths parameter."""
        with patch('src.vectorstores.faiss.HuggingFaceEmbeddings') as mock_hf:
            mock_hf.return_value = Mock()
            
            db = FAISSVectorDatabase(
                embeddings_type="HF",
                embeddings_model_name="test-model"
            )
            
            with pytest.raises(ValueError, match="folder_paths must be a list"):
                db.add_html(folder_paths="not_a_list")

    @patch('src.vectorstores.faiss.process_pdf_docs')
    def test_add_documents_pdf_success(self, mock_process_pdf):
        """Test successful addition of PDF documents."""
        mock_documents = [
            Document(page_content="Test PDF content", metadata={"source": "test.pdf"})
        ]
        mock_process_pdf.return_value = mock_documents
        
        with patch('src.vectorstores.faiss.HuggingFaceEmbeddings') as mock_hf:
            with patch('src.vectorstores.faiss.FAISS') as mock_faiss:
                mock_hf.return_value = Mock()
                mock_faiss.from_documents.return_value = Mock()
                
                db = FAISSVectorDatabase(
                    embeddings_type="HF",
                    embeddings_model_name="test-model"
                )
                
                result = db.add_documents(
                    folder_paths=["test.pdf"],
                    file_type="pdf",
                    return_docs=True
                )
                
                assert result == mock_documents
                assert len(db.processed_docs) == 1
                mock_process_pdf.assert_called_once_with(file_path="test.pdf")

    def test_add_documents_invalid_file_type(self):
        """Test add_documents with invalid file type."""
        with patch('src.vectorstores.faiss.HuggingFaceEmbeddings') as mock_hf:
            mock_hf.return_value = Mock()
            
            db = FAISSVectorDatabase(
                embeddings_type="HF",
                embeddings_model_name="test-model"
            )
            
            with pytest.raises(ValueError, match="File type not supported"):
                db.add_documents(
                    folder_paths=["test.txt"],
                    file_type="txt"
                )

    def test_add_documents_invalid_folder_paths(self):
        """Test add_documents with invalid folder_paths parameter."""
        with patch('src.vectorstores.faiss.HuggingFaceEmbeddings') as mock_hf:
            mock_hf.return_value = Mock()
            
            db = FAISSVectorDatabase(
                embeddings_type="HF",
                embeddings_model_name="test-model"
            )
            
            with pytest.raises(ValueError, match="folder_paths must be a list"):
                db.add_documents(folder_paths="not_a_list", file_type="pdf")

    @patch('src.vectorstores.faiss.FAISS')
    def test_get_documents(self, mock_faiss):
        """Test getting documents from database."""
        mock_faiss_instance = Mock()
        mock_faiss.from_documents.return_value = mock_faiss_instance
        
        # Mock the docstore with documents
        mock_doc1 = Mock()
        mock_doc2 = Mock()
        mock_faiss_instance.docstore._dict.values.return_value = [mock_doc1, mock_doc2]
        
        with patch('src.vectorstores.faiss.HuggingFaceEmbeddings') as mock_hf:
            mock_hf.return_value = Mock()
            
            db = FAISSVectorDatabase(
                embeddings_type="HF",
                embeddings_model_name="test-model"
            )
            
            # Add documents to create database
            documents = [
                Document(page_content="Test content", metadata={"source": "test"})
            ]
            db._add_to_db(documents)
            
            result = list(db.get_documents())
            
            assert len(result) == 2
            assert mock_doc1 in result
            assert mock_doc2 in result

    @patch('src.vectorstores.faiss.generate_knowledge_base')
    @patch('src.vectorstores.faiss.FAISS')
    def test_process_json(self, mock_faiss, mock_generate_kb):
        """Test processing JSON files."""
        mock_documents = [
            Document(page_content="JSON content", metadata={"source": "test.json"})
        ]
        mock_generate_kb.return_value = mock_documents
        
        mock_faiss_instance = Mock()
        mock_faiss.from_documents.return_value = mock_faiss_instance
        
        with patch('src.vectorstores.faiss.HuggingFaceEmbeddings') as mock_hf:
            mock_hf.return_value = Mock()
            
            db = FAISSVectorDatabase(
                embeddings_type="HF",
                embeddings_model_name="test-model"
            )
            
            result = db.process_json(["test.json"])
            
            assert result is mock_faiss_instance
            mock_generate_kb.assert_called_once_with(["test.json"])
            mock_faiss.from_documents.assert_called_once()

    def test_process_json_invalid_folder_paths(self):
        """Test process_json with invalid folder_paths parameter."""
        with patch('src.vectorstores.faiss.HuggingFaceEmbeddings') as mock_hf:
            mock_hf.return_value = Mock()
            
            db = FAISSVectorDatabase(
                embeddings_type="HF",
                embeddings_model_name="test-model"
            )
            
            with pytest.raises(ValueError, match="folder_paths must be a list"):
                db.process_json("not_a_list")

    @patch('src.vectorstores.faiss.process_md')
    def test_add_md_docs_no_documents_processed(self, mock_process_md):
        """Test add_md_docs when no documents are processed."""
        mock_process_md.return_value = []  # Empty list
        
        with patch('src.vectorstores.faiss.HuggingFaceEmbeddings') as mock_hf:
            mock_hf.return_value = Mock()
            
            db = FAISSVectorDatabase(
                embeddings_type="HF",
                embeddings_model_name="test-model"
            )
            
            result = db.add_md_docs(
                folder_paths=["empty_folder"],
                return_docs=True
            )
            
            # Should return empty list when no documents processed
            assert result == []
            assert len(db.processed_docs) == 0
            assert db.faiss_db is None

    @patch('src.vectorstores.faiss.process_md')
    def test_add_md_manpages_no_documents_processed(self, mock_process_md):
        """Test add_md_manpages when no documents are processed."""
        mock_process_md.return_value = []  # Empty list
        
        with patch('src.vectorstores.faiss.HuggingFaceEmbeddings') as mock_hf:
            mock_hf.return_value = Mock()
            
            db = FAISSVectorDatabase(
                embeddings_type="HF",
                embeddings_model_name="test-model"
            )
            
            result = db.add_md_manpages(
                folder_paths=["empty_folder"],
                return_docs=True
            )
            
            # Should return empty list when no documents processed
            assert result == []
            assert len(db.processed_docs) == 0
            assert db.faiss_db is None

    @patch('src.vectorstores.faiss.process_html')
    def test_add_html_no_documents_processed(self, mock_process_html):
        """Test add_html when no documents are processed."""
        mock_process_html.return_value = []  # Empty list
        
        with patch('src.vectorstores.faiss.HuggingFaceEmbeddings') as mock_hf:
            mock_hf.return_value = Mock()
            
            db = FAISSVectorDatabase(
                embeddings_type="HF",
                embeddings_model_name="test-model"
            )
            
            result = db.add_html(
                folder_paths=["empty_folder"],
                return_docs=True
            )
            
            # Should return empty list when no documents processed
            assert result == []
            assert len(db.processed_docs) == 0
            assert db.faiss_db is None

    @patch('src.vectorstores.faiss.process_pdf_docs')
    def test_add_documents_no_documents_processed(self, mock_process_pdf):
        """Test add_documents when no documents are processed."""
        mock_process_pdf.return_value = []  # Empty list
        
        with patch('src.vectorstores.faiss.HuggingFaceEmbeddings') as mock_hf:
            mock_hf.return_value = Mock()
            
            db = FAISSVectorDatabase(
                embeddings_type="HF",
                embeddings_model_name="test-model"
            )
            
            result = db.add_documents(
                folder_paths=["empty.pdf"],
                file_type="pdf",
                return_docs=True
            )
            
            # Should return empty list when no documents processed
            assert result == []
            assert len(db.processed_docs) == 0
            assert db.faiss_db is None