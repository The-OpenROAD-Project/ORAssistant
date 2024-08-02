from langchain_community.vectorstores import FAISS
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_community.vectorstores.utils import DistanceStrategy
from langchain.docstore.document import Document

from ..tools.process_md import process_md
from ..tools.process_pdf import process_pdf_docs
from ..tools.process_html import process_html
from ..tools.process_json import generate_knowledge_base

from typing import Optional, Union


class FAISSVectorDatabase:
    def __init__(
        self,
        embeddings_type: str,
        embeddings_model_name: str,
        distance_strategy: DistanceStrategy = DistanceStrategy.COSINE,
        print_progress: bool = False,
        debug: bool = False,
        use_cuda: bool = False,
    ):
        self.embeddings_model_name = embeddings_model_name

        model_kwargs = {'device': 'cuda'} if use_cuda else {}

        self.embedding_model: Union[HuggingFaceEmbeddings, GoogleGenerativeAIEmbeddings]

        if embeddings_type == 'GOOGLE':
            self.embedding_model = GoogleGenerativeAIEmbeddings(
                model=self.embeddings_model_name,
                task_type='retrieval_document',
            )

        elif embeddings_type == 'HF':
            self.embedding_model = HuggingFaceEmbeddings(
                model_name=self.embeddings_model_name,
                multi_process=False,
                encode_kwargs={'normalize_embeddings': True},
                model_kwargs=model_kwargs,
            )

        else:
            raise ValueError('Invalid embdeddings type specified.')

        self.print_progress = print_progress
        self.debug = debug
        self.distance_strategy = distance_strategy

        self._faiss_db = FAISS.from_documents(
            documents=[Document(page_content='')],
            embedding=self.embedding_model,
            distance_strategy=self.distance_strategy,
        )

    @property
    def faiss_db(self) -> FAISS:
        return self._faiss_db

    def add_md_docs(
        self, folder_paths: list[str], chunk_size: int = 500, return_docs: bool = False
    ) -> Optional[list[Document]]:
        if self.print_progress:
            print('Processing markdown docs...')

        docs_processed: list[Document] = []

        for folder_path in folder_paths:
            if self.print_progress:
                print(f'Processing [{folder_path}]...')
            docs_processed.extend(
                process_md(
                    folder_path=folder_path,
                    chunk_size=chunk_size,
                    split_text=True,
                )
            )

        if docs_processed:
            if self.print_progress:
                print(f'Adding {folder_paths} to FAISS database...')
            self._faiss_db.add_documents(docs_processed)
        else:
            raise ValueError('No markdown documents processed.')

        if return_docs:
            return docs_processed

        return None

    def add_md_manpages(
        self, folder_paths: list[str], return_docs: bool = False
    ) -> Optional[list[Document]]:
        if self.print_progress:
            print('Processing markdown manpages...')

        docs_processed: list[Document] = []

        for file_path in folder_paths:
            if self.print_progress:
                print(f'Processing [{file_path}]...')
            docs_processed.extend(process_md(folder_path=file_path, split_text=False))

        if docs_processed:
            if self.print_progress:
                print(f'Adding {folder_paths} to FAISS database...')
            self._faiss_db.add_documents(docs_processed)
        else:
            raise ValueError('No manpages documents processed.')

        if return_docs:
            return docs_processed

        return None

    def add_html(
        self, folder_paths: list[str], return_docs: bool = False
    ) -> Optional[list[Document]]:
        if self.print_progress:
            print('Process HTML docs...')

        docs_processed: list[Document] = []
        for folder_path in folder_paths:
            if self.print_progress:
                print(f'Processing [{folder_path}]...')
                docs_processed.extend(process_html(folder_path=folder_path))

        if docs_processed:
            if self.print_progress:
                print(f'Adding {folder_paths} to FAISS database...')
            self._faiss_db.add_documents(docs_processed)
        else:
            raise ValueError('No HTML docs processed.')

        if return_docs:
            return docs_processed

        return None

    def add_documents(
        self, file_paths: list[str], file_type: str, return_docs: bool = False
    ) -> Optional[list[Document]]:
        if self.print_progress:
            print('Processing docs...')

        docs_processed: list[Document] = []

        for file_path in file_paths:
            if self.print_progress:
                print(f'Processing [{file_path}]...')
            if file_type == 'pdf':
                docs_processed.extend(process_pdf_docs(file_path=file_path))
            else:
                raise ValueError('File type not supported.')

        if docs_processed:
            if self.print_progress:
                print(f'Adding [{file_paths}] to FAISS database...')
            self._faiss_db.add_documents(docs_processed)
        else:
            raise ValueError('No PDF documents processed.')

        if return_docs:
            return docs_processed

        return None

    def process_json(self, folder_paths: list[str]) -> FAISS:
        if self.print_progress:
            print('Processing json files...')

        embeddings = self.embedding_model
        json_docs_processed = generate_knowledge_base(folder_paths)
        json_vector_db = FAISS.from_documents(
            json_docs_processed, embeddings, distance_strategy=DistanceStrategy.COSINE
        )
        return json_vector_db

    def get_relevant_documents(self, query: str, k: int = 2) -> str:
        retrieved_docs = self._faiss_db.similarity_search(query=query, k=k)
        retrieved_text = ''

        for doc in retrieved_docs:
            retrieved_text += doc.page_content.replace('\n', '') + '\n\n'

        return retrieved_text
