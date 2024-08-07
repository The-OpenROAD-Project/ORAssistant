import os
import glob
import json
import logging

from tqdm import tqdm
from typing import Optional

from langchain.docstore.document import Document
from langchain_community.document_loaders import UnstructuredHTMLLoader

from langchain_text_splitters import RecursiveCharacterTextSplitter

from .chunk_documents import chunk_documents

logging.basicConfig(level=os.environ.get('LOGLEVEL', 'INFO').upper())

chunk_size: int = int(os.getenv('CHUNK_SIZE', 4000))
chunk_overlap: int = int(os.getenv('CHUNK_OVERLAP', 400))

text_splitter = RecursiveCharacterTextSplitter(
    chunk_size=chunk_size,
    chunk_overlap=chunk_overlap,
    length_function=len,
    is_separator_regex=False,
)


def process_html(
    folder_path: str,
    split_text: bool = True,
    chunk_size: Optional[int] = None,
) -> list[Document]:
    """
    For processing OR/ORFS docs
    """
    if not os.path.exists(folder_path) or not os.listdir(folder_path):
        logging.error(f'{folder_path} is not populated, returning empty list.')
        return []

    with open('src/source_list.json') as f:
        src_dict = json.loads(f.read())

    html_files = glob.glob(os.path.join(folder_path, '**/*.html'), recursive=True)

    documents = []
    for file_path in tqdm(html_files, desc='Loading HTML files'):
        content = UnstructuredHTMLLoader(file_path=file_path).load()
        for doc in content:
            doc.metadata['source'] = file_path.split('./')[-1]
        documents.extend(content)

    for doc in documents:
        try:
            url = src_dict[doc.metadata['source']]
        except KeyError:
            logging.warn(f"Could not find source for {doc.metadata['source']}")
            url = ''

        new_metadata = {
            'url': url,
            'source': doc.metadata['source'],
        }
        doc.metadata = new_metadata

    if split_text:
        if not chunk_size:
            raise ValueError('Chunk size not set.')

        documents = text_splitter.split_documents(documents)
        docs_chunked = chunk_documents(chunk_size, documents)

        return docs_chunked

    else:
        return documents
