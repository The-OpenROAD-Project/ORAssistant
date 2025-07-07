import pytest
from unittest.mock import Mock, patch
from langchain.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

from src.chains.base_chain import BaseChain


class TestBaseChain:
    """Test suite for BaseChain class."""

    def test_init_with_all_parameters(self):
        """Test BaseChain initialization with all parameters."""
        mock_llm = Mock()
        mock_vector_db = Mock()
        prompt_template = "Test prompt: {query}"
        
        chain = BaseChain(
            llm_model=mock_llm,
            vector_db=mock_vector_db,
            prompt_template_str=prompt_template
        )
        
        assert chain.llm_model == mock_llm
        assert chain.vector_db == mock_vector_db
        assert isinstance(chain.prompt_template, ChatPromptTemplate)
        assert chain.llm_chain is None

    def test_init_with_no_parameters(self):
        """Test BaseChain initialization with no parameters."""
        chain = BaseChain()
        
        assert chain.llm_model is None
        assert chain.vector_db is None
        assert chain.llm_chain is None
        assert not hasattr(chain, 'prompt_template')

    def test_init_with_prompt_template_only(self):
        """Test BaseChain initialization with only prompt template."""
        prompt_template = "Test prompt: {query}"
        
        chain = BaseChain(prompt_template_str=prompt_template)
        
        assert chain.llm_model is None
        assert chain.vector_db is None
        assert isinstance(chain.prompt_template, ChatPromptTemplate)
        assert chain.llm_chain is None

    def test_create_llm_chain(self):
        """Test creating LLM chain."""
        mock_llm = Mock()
        prompt_template = "Test prompt: {query}"
        
        chain = BaseChain(
            llm_model=mock_llm,
            prompt_template_str=prompt_template
        )
        
        chain.create_llm_chain()
        
        assert chain.llm_chain is not None

    def test_get_llm_chain_creates_chain_if_none(self):
        """Test get_llm_chain creates chain if it doesn't exist."""
        mock_llm = Mock()
        prompt_template = "Test prompt: {query}"
        
        chain = BaseChain(
            llm_model=mock_llm,
            prompt_template_str=prompt_template
        )
        
        # Chain should be None initially
        assert chain.llm_chain is None
        
        # Getting the chain should create it
        result = chain.get_llm_chain()
        
        assert result is not None
        assert chain.llm_chain is not None

    def test_get_llm_chain_returns_existing_chain(self):
        """Test get_llm_chain returns existing chain if it exists."""
        mock_llm = Mock()
        prompt_template = "Test prompt: {query}"
        
        chain = BaseChain(
            llm_model=mock_llm,
            prompt_template_str=prompt_template
        )
        
        # Create the chain first
        chain.create_llm_chain()
        existing_chain = chain.llm_chain
        
        # Getting the chain should return the same instance
        result = chain.get_llm_chain()
        
        assert result is existing_chain

    def test_chain_creation_without_prompt_template_raises_error(self):
        """Test that creating chain without prompt template raises error."""
        mock_llm = Mock()
        
        chain = BaseChain(llm_model=mock_llm)
        
        with pytest.raises(AttributeError):
            chain.create_llm_chain()

    def test_chain_creation_without_llm_model_raises_error(self):
        """Test that creating chain without LLM model raises error."""
        prompt_template = "Test prompt: {query}"
        
        chain = BaseChain(prompt_template_str=prompt_template)
        
        with pytest.raises(TypeError):
            chain.create_llm_chain()

    @pytest.mark.unit
    def test_vector_db_assignment(self):
        """Test vector database assignment."""
        mock_vector_db = Mock()
        
        chain = BaseChain(vector_db=mock_vector_db)
        
        assert chain.vector_db is mock_vector_db

    @pytest.mark.unit
    def test_prompt_template_creation(self):
        """Test prompt template creation from string."""
        prompt_template_str = "Answer the following question: {query}"
        
        chain = BaseChain(prompt_template_str=prompt_template_str)
        
        assert hasattr(chain, 'prompt_template')
        assert isinstance(chain.prompt_template, ChatPromptTemplate)
        
        # Test that the template can be formatted
        formatted = chain.prompt_template.format(query="What is OpenROAD?")
        assert "What is OpenROAD?" in formatted