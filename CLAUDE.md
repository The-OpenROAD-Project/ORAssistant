# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

### Development Environment Setup
```bash
# Initialize all components with dev dependencies
make init-dev

# Initialize individual components
cd backend && make init-dev
cd frontend && make init-dev
cd evaluation && make init-dev
```

### Code Quality
```bash
# Format all code
make format

# Run all checks (linting, type checking, pre-commit)
make check

# Individual component checks
cd backend && make check  # mypy + ruff
cd frontend && make check  # mypy + ruff  
cd evaluation && make check  # mypy + ruff
```

### Backend Development
```bash
# Run the FastAPI server
cd backend && python main.py

# Run terminal chatbot
cd backend && python chatbot.py

# Build documentation dataset
cd backend && python build_docs.py
```

### Frontend Development
```bash
# Run Streamlit app
cd frontend && streamlit run streamlit_app.py
```

### Evaluation
```bash
# Run LLM evaluation tests
cd evaluation && make llm-tests
```

### Docker
```bash
# Start all services
make docker-up

# Stop all services
make docker-down
```

## Architecture

This is a RAG-based conversational assistant for OpenROAD with three main components:

### Backend (`backend/`)
- **FastAPI server** with chat endpoints
- **LangGraph-based routing** - Routes queries to specialized retrievers based on query classification
- **Multiple retriever tools** for different content types:
  - General OR/ORFS information
  - OR tools and commands  
  - Installation docs
  - Error messages
  - OpenSTA docs
  - Yosys docs
  - Klayout docs
- **FAISS vector databases** for document retrieval
- **Hybrid retrieval** combining semantic search, MMR, and BM25
- **Cross-encoder reranking** for improved relevance

### Frontend (`frontend/`)
- **Streamlit-based chat interface**
- **User feedback collection** via Google Sheets API
- **MongoDB integration** for data persistence

### Evaluation (`evaluation/`)
- **Automated LLM evaluation** using various metrics
- **Human evaluation interface** for research
- **Performance benchmarking** tools

## Key Files

- `backend/src/agents/retriever_graph.py` - Main LangGraph routing logic
- `backend/src/chains/` - Individual retriever implementations
- `backend/build_docs.py` - Documentation dataset builder
- `backend/src/vectorstores/faiss.py` - Vector database implementation
- `frontend/streamlit_app.py` - Main Streamlit interface
- `evaluation/auto_evaluation/eval_main.py` - Automated evaluation runner

## Development Guidelines

- Use **Python 3.12** with virtual environments
- Follow **ruff** formatting and linting standards
- Run **mypy** for type checking
- Use **pre-commit hooks** for code quality
- Components are designed to be **independently deployable**

## Dataset

The RAG dataset is hosted on HuggingFace and contains:
- OpenROAD documentation
- OpenROAD-flow-scripts documentation  
- OpenSTA documentation
- Yosys documentation
- Klayout documentation
- GitHub discussions and issues

Download with:
```bash
huggingface-cli download The-OpenROAD-Project/ORAssistant_RAG_Dataset --repo-type dataset --local-dir data/
```