import os
import json
from dotenv import load_dotenv

from langchain.docstore.document import Document
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter

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
    docs = loader.load_and_split(text_splitter=text_splitter)

    with open('src/source_list.json') as f:
        src_dict = json.loads(f.read())

    for doc in docs:
        doc.metadata['source'] = src_dict.get(
            doc.metadata['source'], doc.metadata['source']
        )

    return docs
