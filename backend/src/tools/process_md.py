import json
import os

from langchain.text_splitter import RecursiveCharacterTextSplitter, Language
from langchain.docstore.document import Document as LangchainDocument
from langchain_community.document_loaders import DirectoryLoader

from .recursive_chunk import recursive_chunking


def chunk_md_docs(
    embeddings_model_name: str, files_path: str, chunk_size: int
) -> list[LangchainDocument]:
    """
    For processing OR/ORFS docs
    """
    # if no files in the directory
    if not os.path.exists(files_path) or not os.listdir(files_path):
        print(f"{files_path} is not populated, returning empty list.")
        return []

    with open("src/source_list.json") as f:
        src_dict = json.loads(f.read())

    loader = DirectoryLoader(files_path, glob="**/*.md", show_progress=True)
    documents = loader.load()

    markdown_splitter = RecursiveCharacterTextSplitter.from_language(
        chunk_size=chunk_size,
        chunk_overlap=int(chunk_size / 10),
        add_start_index=True,
        strip_whitespace=True,
        language=Language.MARKDOWN,
    )

    documents_knowledge_base = []
    for doc in documents:
        new_metadata = {
            "url": src_dict[doc.metadata["source"]],
            "source": doc.metadata["source"],
        }
        documents_knowledge_base.append(
            LangchainDocument(page_content=doc.page_content, metadata=new_metadata)
        )

    docs_split = []
    for doc in documents_knowledge_base:
        docs_split.extend(markdown_splitter.split_documents([doc]))

    docs_chunked = recursive_chunking(
        int(chunk_size / 2),
        docs_split,
        tokenizer_name=embeddings_model_name,
    )

    return docs_chunked


def chunk_md_manpages(files_path: str) -> list[LangchainDocument]:
    """
    For processing manpages
    """
    # if no files in the directory
    if not os.path.exists(files_path) or not os.listdir(files_path):
        print(f"{files_path} is not populated, returning empty list.")
        return []

    loader = DirectoryLoader(files_path, glob="**/*.md", show_progress=True)
    documents_knowledge_base = loader.load()

    return documents_knowledge_base
