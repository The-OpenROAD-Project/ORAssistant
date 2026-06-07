# Pull pre-built FAISS indices from the cache image (built by the build-faiss CI workflow).
# This avoids rebuilding indices on every PR — only the secret CI rebuilds them.
ARG FAISS_CACHE_IMAGE=ghcr.io/the-openroad-project/orassistant-faiss-cache:latest
FROM ${FAISS_CACHE_IMAGE} AS faiss-cache

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

# Copy pre-built FAISS indices from the cache image.
# HybridRetrieverChain detects faiss_db/<name> at startup and takes the fast load_db()
# path, reducing graph init from ~60 min to a few seconds.
COPY --from=faiss-cache /ORAssistant-backend/faiss_db ./faiss_db

# Runtime embedding model must match the model used when building the indices.
# Override via docker run -e or docker-compose environment if using a different model.
ENV EMBEDDINGS_TYPE=HF
ENV HF_EMBEDDINGS=thenlper/gte-large

EXPOSE 8000

CMD ["uv", "run", "uvicorn", "src.api.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
