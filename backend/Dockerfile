FROM ghcr.io/astral-sh/uv:python3.13-bookworm-slim

WORKDIR /ORAssistant-backend

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

RUN pip install uv

COPY ./pyproject.toml /ORAssistant-backend/pyproject.toml
COPY . .

RUN uv venv .venv && uv sync --dev && uv run /ORAssistant-backend/src/post_install.py

RUN git clone https://huggingface.co/datasets/The-OpenROAD-Project/ORAssistant_RAG_Dataset && \
    mkdir -p data && \
    mv ORAssistant_RAG_Dataset/* data/ && \
    rm -rf ORAssistant_RAG_Dataset

ENV POSTGRES_HOST=postgres \
    POSTGRES_PORT=5432 \
    POSTGRES_USER=orassistant \
    POSTGRES_PASSWORD=password \
    POSTGRES_DB=orassistant_db

EXPOSE 8000

CMD ["uv", "run", "uvicorn", "src.api.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
