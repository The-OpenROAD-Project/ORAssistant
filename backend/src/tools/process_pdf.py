from langchain_community.document_loaders import PyPDFLoader
from langchain.docstore.document import Document

from langchain_text_splitters import RecursiveCharacterTextSplitter

from dotenv import load_dotenv
import os

load_dotenv()

chunk_size: int = int(os.getenv('CHUNK_SIZE', 4000))
chunk_overlap: int = int(os.getenv('CHUNK_OVERLAP', 400))

text_splitter = RecursiveCharacterTextSplitter(
    chunk_size=chunk_size,
    chunk_overlap=chunk_overlap,
    length_function=len,
    is_separator_regex=False,
)


def process_pdf_docs(file_path: str) -> list[Document]:
    loader = PyPDFLoader(file_path)
    pages = loader.load_and_split(text_splitter=text_splitter)
    return pages
