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

# Build FAISS indices into the image using HuggingFace embeddings (no API quota).
# At container startup HybridRetrieverChain detects faiss_db/ and loads from disk,
# reducing graph init from ~60 min to a few seconds.
# Override these ARGs to build with a different model when needed.
ARG BUILD_EMBEDDINGS_TYPE=HF
ARG BUILD_HF_MODEL=thenlper/gte-large
RUN PYTHONPATH=/ORAssistant-backend \
    EMBEDDINGS_TYPE=${BUILD_EMBEDDINGS_TYPE} \
    HF_EMBEDDINGS=${BUILD_HF_MODEL} \
    FAST_MODE=true \
    uv run python scripts/build_faiss.py

# Set HF as the default embedding backend so runtime matches the pre-built indices.
# Override at container runtime (docker run -e / docker-compose environment) if needed.
ENV EMBEDDINGS_TYPE=HF
ENV HF_EMBEDDINGS=thenlper/gte-large

EXPOSE 8000

CMD ["uv", "run", "uvicorn", "src.api.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
