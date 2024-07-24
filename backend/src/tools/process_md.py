import json
import os
import glob
from tqdm import tqdm

from bs4 import BeautifulSoup
import markdown as md

from dotenv import load_dotenv

from langchain.docstore.document import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter

from .chunk_documents import chunk_documents

load_dotenv()

chunk_size: int = int(os.getenv('CHUNK_SIZE', 4000))
chunk_overlap: int = int(os.getenv('CHUNK_OVERLAP', 400))

text_splitter = RecursiveCharacterTextSplitter(
    chunk_size=chunk_size,
    chunk_overlap=chunk_overlap,
    length_function=len,
    is_separator_regex=False,
)


def md_to_text(md_content: str) -> str:
    html = md.markdown(md_content)
    soup = BeautifulSoup(html, features='html.parser')
    return soup.get_text()


def load_docs(folder_path: str) -> list[Document]:
    md_files = glob.glob(os.path.join(folder_path, '**/*.md'), recursive=True)
    documents = []
    for file_path in tqdm(md_files, desc='Loading Markdown files'):
        with open(file_path, 'r', encoding='utf-8') as file:
            content = md_to_text(file.read())
            metadata = {'source': file_path[2:]}
            documents.append(Document(page_content=content, metadata=metadata))
    return documents


def process_md_docs(
    embeddings_model_name: str, folder_path: str, chunk_size: int
) -> list[Document]:
    """
    For processing OR/ORFS docs
    """
    # if no files in the directory
    if not os.path.exists(folder_path) or not os.listdir(folder_path):
        print(f'{folder_path} is not populated, returning empty list.')
        return []

    with open('src/source_list.json') as f:
        src_dict = json.loads(f.read())

    documents = load_docs(folder_path=folder_path)
    documents = text_splitter.split_documents(documents)

    documents_knowledge_base = []
    for doc in documents:
        try:
            url = src_dict[doc.metadata['source']]
        except KeyError:
            print(f"Cound not find source for {doc.metadata['source']}")
            url = ''

        new_metadata = {
            'url': url,
            'source': doc.metadata['source'],
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


def process_md_manpages(folder_path: str) -> list[Document]:
    """
    For processing manpages
    """
    # if no files in the directory
    if not os.path.exists(folder_path) or not os.listdir(folder_path):
        print(f'{folder_path} is not populated, returning empty list.')
        return []

    documents = load_docs(folder_path=folder_path)

    return documents
