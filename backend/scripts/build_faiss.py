"""
Pre-build FAISS indices at Docker image build time with per-index incremental skipping.

Each index has a hash computed from its source file paths + sizes. If the hash matches
the stored manifest and the index directory already exists, that index is skipped.
Only changed or missing indices are rebuilt, so the secret CI only pays for what changed.

Run from /ORAssistant-backend (the WORKDIR in the Dockerfile) so data/ is reachable.
EMBEDDINGS_TYPE and HF_EMBEDDINGS are read from the environment.
"""

import hashlib
import json
import logging
import os
import sys
from pathlib import Path

from src.chains.hybrid_retriever_chain import HybridRetrieverChain

logging.basicConfig(level="INFO", format="%(levelname)s %(message)s")

FAISS_DB_DIR = Path("faiss_db")
MANIFEST_FILE = FAISS_DB_DIR / "manifest.json"

embeddings_type = os.environ.get("EMBEDDINGS_TYPE", "HF")
hf_embeddings = os.environ.get("HF_EMBEDDINGS", "thenlper/gte-large")
fast_mode = os.environ.get("FAST_MODE", "true").lower() == "true"
chunk_size = int(os.environ.get("CHUNK_SIZE", 4000))

if not os.path.isdir("data"):
    sys.exit("ERROR: run from backend directory — data/ not found")

if embeddings_type != "HF":
    sys.exit(
        f"ERROR: build_faiss.py only supports EMBEDDINGS_TYPE=HF, got '{embeddings_type}'"
    )

embeddings_config = {"type": embeddings_type, "name": hf_embeddings}

_MD = "./data/markdown"
_HTML = "./data/html"

# Mirrors fastmode_docs_map / markdown_docs_map in retriever_tools.py.
# Each entry must use the same paths and index_name as RetrieverTools.initialize().
INDEX_DEFS: dict[bool, list[dict]] = {
    True: [  # fast_mode=True
        {"name": "general", "markdown_docs_path": [f"{_MD}/OR_docs"]},
        {"name": "install", "markdown_docs_path": [f"{_MD}/ORFS_docs/installation"]},
        {"name": "commands", "markdown_docs_path": [f"{_MD}/OR_docs/tools"]},
        {
            "name": "yosys_rtdocs",
            "html_docs_path": [
                f"{_HTML}/yosys_docs/yosyshq.readthedocs.io"
                "/projects/yosys/en/latest/getting_started"
            ],
        },
        {
            "name": "klayout",
            "html_docs_path": [f"{_HTML}/klayout_docs/www.klayout.de/examples"],
        },
        {"name": "errinfo", "markdown_docs_path": [f"{_MD}/gh_discussions/Bug"]},
    ],
    False: [  # fast_mode=False (full dataset)
        {
            "name": "general",
            "markdown_docs_path": [
                f"{_MD}/OR_docs",
                f"{_MD}/ORFS_docs",
                f"{_MD}/gh_discussions",
                f"{_MD}/manpages/man1",
                f"{_MD}/manpages/man2",
                f"{_MD}/OpenSTA_docs",
            ],
            "html_docs_path": [f"{_HTML}/or_website/"],
            "other_docs_path": ["./data/pdf"],
        },
        {
            "name": "install",
            "markdown_docs_path": [
                f"{_MD}/ORFS_docs/installation",
                f"{_MD}/OR_docs/installation",
                f"{_MD}/gh_discussions/Build",
                f"{_MD}/gh_discussions/Installation",
                f"{_MD}/OpenSTA_docs",
            ],
        },
        {
            "name": "commands",
            "markdown_docs_path": [
                f"{_MD}/OR_docs/tools",
                f"{_MD}/ORFS_docs/general",
                f"{_MD}/gh_discussions/Query",
                f"{_MD}/gh_discussions/Runtime",
                f"{_MD}/gh_discussions/Documentation",
                f"{_MD}/manpages/man1",
                f"{_MD}/manpages/man2",
                f"{_MD}/OpenSTA_docs",
            ],
            "other_docs_path": ["./data/pdf"],
        },
        {"name": "yosys_rtdocs", "html_docs_path": [f"{_HTML}/yosys_docs"]},
        {"name": "klayout", "html_docs_path": [f"{_HTML}/klayout_docs"]},
        {
            "name": "errinfo",
            "markdown_docs_path": [
                f"{_MD}/manpages/man3",
                f"{_MD}/gh_discussions/Bug",
            ],
        },
    ],
}


def _source_paths(index_def: dict) -> list[str]:
    paths: list[str] = []
    for key in ("markdown_docs_path", "html_docs_path", "other_docs_path"):
        paths.extend(index_def.get(key, []))
    return paths


def _hash_paths(paths: list[str]) -> str:
    """Stable hash over file path + size for all files under the given directories."""
    h = hashlib.sha256()
    for base in sorted(p for p in paths if Path(p).exists()):
        for f in sorted(Path(base).rglob("*")):
            if f.is_file() and not f.name.startswith("."):
                h.update(str(f.relative_to(Path(base))).encode())
                h.update(str(f.stat().st_size).encode())
    return h.hexdigest()


def _load_manifest() -> dict:
    if MANIFEST_FILE.exists():
        return json.loads(MANIFEST_FILE.read_text())
    return {}


def _save_manifest(manifest: dict) -> None:
    FAISS_DB_DIR.mkdir(exist_ok=True)
    MANIFEST_FILE.write_text(json.dumps(manifest, indent=2))


logging.info(
    "Pre-building FAISS indices (fast_mode=%s, model=%s)", fast_mode, hf_embeddings
)

manifest = _load_manifest()
updated = False

for index_def in INDEX_DEFS[fast_mode]:
    name: str = index_def["name"]
    paths = _source_paths(index_def)
    current_hash = _hash_paths(paths)
    index_dir = FAISS_DB_DIR / name

    if manifest.get(name) == current_hash and index_dir.is_dir():
        logging.info("Skipping %s (source data unchanged)", name)
        continue

    logging.info("Building index: %s", name)
    chain = HybridRetrieverChain(
        embeddings_config=embeddings_config,
        reranking_model_name="",
        use_cuda=False,
        index_name=name,
        markdown_docs_path=index_def.get("markdown_docs_path"),
        html_docs_path=index_def.get("html_docs_path"),
        other_docs_path=index_def.get("other_docs_path"),
        chunk_size=chunk_size,
        contextual_rerank=False,
    )
    chain.create_hybrid_retriever()
    manifest[name] = current_hash
    updated = True
    logging.info("Built index: %s", name)

if updated:
    _save_manifest(manifest)
    logging.info("FAISS pre-build complete (manifest updated)")
else:
    logging.info("FAISS pre-build complete (all indices up to date, nothing rebuilt)")
