import json
import os
import glob
from tqdm import tqdm

from bs4 import BeautifulSoup
import markdown as md

from langchain.docstore.document import Document

from .chunk_documents import chunk_documents


def md_to_text(md_content: str) -> str:
    html = md.markdown(md_content)
    soup = BeautifulSoup(html, features="html.parser")
    return soup.get_text()


def load_docs(files_path: str) -> list[Document]:
    md_files = glob.glob(os.path.join(files_path, "**/*.md"), recursive=True)
    documents = []
    for file_path in tqdm(md_files, desc="Loading Markdown files"):
        with open(file_path, "r", encoding="utf-8") as file:
            content = md_to_text(file.read())
            metadata = {"source": file_path[2:]}
            documents.append(Document(page_content=content, metadata=metadata))
    return documents


def process_md_docs(
    embeddings_model_name: str, files_path: str, chunk_size: int
) -> list[Document]:
    """
    For processing OR/ORFS docs
    """
    # if no files in the directory
    if not os.path.exists(files_path) or not os.listdir(files_path):
        print(f"{files_path} is not populated, returning empty list.")
        return []

    with open("src/source_list.json") as f:
        src_dict = json.loads(f.read())

    documents = load_docs(files_path=files_path)

    with open("documents.txt", "w") as f:
        for i, doc in enumerate(documents):
            f.write(f"Doc ID: {i + 1}\n")
            f.write(str(doc.page_content) + "\n")

    documents_knowledge_base = []
    for doc in documents:
        new_metadata = {
            "url": src_dict[doc.metadata["source"]],
            "source": doc.metadata["source"],
        }
        documents_knowledge_base.append(
            Document(page_content=doc.page_content, metadata=new_metadata)
        )

    docs_chunked = chunk_documents(
        chunk_size,
        documents_knowledge_base,
        tokenizer_name=embeddings_model_name,
    )

    return docs_chunked


def process_md_manpages(files_path: str) -> list[Document]:
    """
    For processing manpages
    """
    # if no files in the directory
    if not os.path.exists(files_path) or not os.listdir(files_path):
        print(f"{files_path} is not populated, returning empty list.")
        return []

    documents = load_docs(files_path=files_path)

    return documents
