"""
Pre-build FAISS indices for all retriever chains at Docker image build time.

Run from /ORAssistant-backend (the WORKDIR in the Dockerfile) so that data/ is
reachable via relative paths.  Uses HuggingFace embeddings by default so no
external API key or network quota is required during docker build.

The saved indices land in faiss_db/ inside the image.  At container startup,
HybridRetrieverChain.create_hybrid_retriever() detects existing directories and
takes the load_db() path instead of re-embedding, dropping init time from ~60 min
to a few seconds.

EMBEDDINGS_TYPE and HF_EMBEDDINGS are read from the environment so the Dockerfile
ARG values propagate through cleanly.
"""

import os
import sys
import logging

logging.basicConfig(level="INFO", format="%(levelname)s %(message)s")

if not os.path.isdir("data"):
    sys.exit("ERROR: run from backend directory — data/ not found")

embeddings_type = os.environ.get("EMBEDDINGS_TYPE", "HF")
hf_embeddings = os.environ.get("HF_EMBEDDINGS", "thenlper/gte-large")
fast_mode = os.environ.get("FAST_MODE", "true").lower() == "true"

if embeddings_type != "HF":
    sys.exit(
        f"ERROR: build_faiss.py only supports EMBEDDINGS_TYPE=HF, got '{embeddings_type}'"
    )

embeddings_config = {"type": embeddings_type, "name": hf_embeddings}

logging.info("Pre-building FAISS indices")
logging.info("  model     : %s", hf_embeddings)
logging.info("  fast_mode : %s", fast_mode)

from src.agents.retriever_tools import RetrieverTools

tools = RetrieverTools()
tools.initialize(
    embeddings_config=embeddings_config,
    reranking_model_name="",
    use_cuda=False,
    fast_mode=fast_mode,
    contextual_rerank=False,
)

logging.info("FAISS pre-build complete")
