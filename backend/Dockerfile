FROM ghcr.io/astral-sh/uv:python3.13-bookworm-slim

WORKDIR /ORAssistant-backend

# Install system dependencies (cacheable layer)
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    gcc \
    git \
    git-lfs \
    libpq-dev \
    pandoc \
    postgresql-client \
    wget && \
    git lfs install && \
    rm -rf /var/lib/apt/lists/*

# Install uv (cacheable layer)
RUN pip install uv

# Copy only dependency files first for better caching
COPY ./pyproject.toml ./uv.lock* /ORAssistant-backend/

# Install dependencies (cacheable layer - only rebuilds if dependencies change)
RUN uv venv .venv && uv sync --dev

# Copy the rest of the application
COPY . .

# Run post-install script
RUN uv run /ORAssistant-backend/src/post_install.py

# Download dataset (cacheable layer)
RUN git clone https://huggingface.co/datasets/The-OpenROAD-Project/ORAssistant_RAG_Dataset && \
    mkdir -p data && \
    mv ORAssistant_RAG_Dataset/* data/ && \
    rm -rf ORAssistant_RAG_Dataset

EXPOSE 8000

CMD ["uv", "run", "uvicorn", "src.api.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
