FROM ghcr.io/astral-sh/uv:python3.13-bookworm-slim

WORKDIR /ORAssistant-backend

# Layer 1: system deps
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

# Layer 2: HF dataset
RUN git clone https://huggingface.co/datasets/The-OpenROAD-Project/ORAssistant_RAG_Dataset && \
    mkdir -p data && \
    mv ORAssistant_RAG_Dataset/* data/ && \
    rm -rf ORAssistant_RAG_Dataset

# Layer 3: Python dep manifests
COPY ./pyproject.toml /ORAssistant-backend/pyproject.toml
COPY ./uv.lock /ORAssistant-backend/uv.lock

# Layer 4: Install Python deps
RUN uv venv .venv && uv sync --dev

# Layer 5: Source code
COPY . .

# Layer 6: Post install
RUN uv run /ORAssistant-backend/src/post_install.py

EXPOSE 8000

CMD ["uv", "run", "uvicorn", "src.api.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
