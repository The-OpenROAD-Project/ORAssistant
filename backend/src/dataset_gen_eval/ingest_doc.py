from pathlib import Path
import json
import uuid
from typing import List

from langchain.text_splitter import RecursiveCharacterTextSplitter
from ..vectorstores.faiss import FAISSVectorDatabase
from ..tools.process_pdf import process_pdf_docs
from ..tools.process_md import process_md

DOMAINS = [
    "general_openroad",
    # "command_reference"
    "installation_guides",
    "error_messages",
    "opensta_yosys_klayout",
]


# discover files in the raw data dir
def discover_files(domain: str) -> List[Path]:
    root = Path(f"data/raw/{domain}")
    # getting all the files
    return list(root.rglob("*.*"))


# document loader function
def load_as_documents(path):
    suffix = path.suffix.lower()
    if suffix == ".pdf":
        return process_pdf_docs(str(path))
    elif suffix in {".md", ".markdown"}:
        return process_md(str(path.parent), split_text=False)
    elif suffix == ".html":
        print("HTML Files skipped for now")
        return []
    else:
        return []


# chunking function
def chunk(docs, size=700, overlap=70):
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=size, chunk_overlap=overlap, add_start_index=True
    )
    out = []
    for d in docs:
        out.extend(splitter.split_documents([d]))
    return out


# adding metadata to each chunk
def enrich_metadata(chunks, domain, source_path):
    for doc in chunks:
        doc.metadata.update(
            {
                "domain": domain,
                "doc_path": str(source_path.relative_to("data/raw")),
                "chunk_id": f"{uuid.uuid4()}",
            }
        )
    return chunks


def build_domain_index(domain):
    vdb = FAISSVectorDatabase(
        embeddings_type="HF",
        embeddings_model_name="sentence-transformers/all-MiniLM-L6-v2",
    )
    manifest = []

    files = discover_files(domain)
    total_files = len(files)
    print(f"Processing {total_files} files for domain: {domain}")

    for idx, fp in enumerate(files):
        print(f"[{idx + 1}/{total_files}] Processing: {fp}")

        if fp.name.startswith("."):
            print(f"Skipping system file: {fp}")
            continue

        docs = load_as_documents(fp)
        if not docs:
            print(f"No documents loaded from: {fp}")
            continue

        chunks = chunk(docs)
        if not chunks:
            print(f"No chunks created from: {fp}")
            continue

        chunks = enrich_metadata(chunks, domain, fp)
        manifest += [c.metadata for c in chunks]

        # Process chunks in smaller batches for better memory management
        batch_size = 50
        for i in range(0, len(chunks), batch_size):
            batch = chunks[i : i + batch_size]
            vdb._add_to_db(batch)
            print(f"  Added batch {i // batch_size + 1} ({len(batch)} chunks)")

    vdb.save_db(name=domain)
    Path("data/manifests").mkdir(exist_ok=True, parents=True)
    with open(f"data/manifests/{domain}.jsonl", "w") as f:
        for row in manifest:
            f.write(json.dumps(row) + "\n")


if __name__ == "__main__":
    for dom in DOMAINS:
        build_domain_index(dom)
    print("All domain indexes built & manifests written.")
