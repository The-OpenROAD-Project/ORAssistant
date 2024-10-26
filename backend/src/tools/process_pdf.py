import os
import json
import logging
from dotenv import load_dotenv
from pypdf.errors import PdfStreamError

from langchain.docstore.document import Document
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter

load_dotenv()

chunk_size: int = int(os.getenv("CHUNK_SIZE", 4000))
chunk_overlap: int = int(os.getenv("CHUNK_OVERLAP", 400))

text_splitter = RecursiveCharacterTextSplitter(
    chunk_size=chunk_size,
    chunk_overlap=chunk_overlap,
    length_function=len,
    is_separator_regex=False,
)


def process_pdf_docs(file_path: str) -> list[Document]:
    loader = PyPDFLoader(file_path)

    with open("data/source_list.json") as f:
        src_dict = json.loads(f.read())

    try:
        documents = loader.load_and_split(text_splitter=text_splitter)
    except PdfStreamError:
        logging.error(f"Error processing PDF: {file_path} is corrupted or incomplete.")

    for doc in documents:
        try:
            doc.metadata["source"] = file_path.split("./")[-1]
            url = src_dict[doc.metadata["source"]]
        except KeyError:
            logging.error(f"Could not find source for {doc.metadata['source']}")
            url = ""

        new_metadata = {
            "url": url,
            "source": doc.metadata["source"],
        }
        doc.metadata = new_metadata

    return documents
