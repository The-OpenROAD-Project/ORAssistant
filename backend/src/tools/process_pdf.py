from langchain_community.document_loaders import PyPDFLoader
from langchain.docstore.document import Document

from langchain_text_splitters import RecursiveCharacterTextSplitter

text_splitter = RecursiveCharacterTextSplitter(
    chunk_size=2000,
    chunk_overlap=200,
    length_function=len,
    is_separator_regex=False,
)


def process_pdf_docs(file_path: str) -> list[Document]:
    loader = PyPDFLoader(file_path)
    pages = loader.load_and_split(text_splitter=text_splitter)
    return pages
