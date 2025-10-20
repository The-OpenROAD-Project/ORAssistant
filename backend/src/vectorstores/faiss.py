import os
import logging
from typing import Optional, Union
from dotenv import load_dotenv

from langchain_community.vectorstores import FAISS
from langchain_community.vectorstores.utils import DistanceStrategy
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_google_vertexai import VertexAIEmbeddings
from langchain.docstore.document import Document

from ..tools.process_md import process_md
from ..tools.process_pdf import process_pdf_docs
from ..tools.process_html import process_html
from ..tools.process_json import generate_knowledge_base

logging.basicConfig(level=os.environ.get("LOGLEVEL", "INFO").upper())

load_dotenv()


class FAISSVectorDatabase:
    def __init__(
        self,
        embeddings_type: str,
        embeddings_model_name: str,
        distance_strategy: DistanceStrategy = DistanceStrategy.COSINE,
        debug: bool = False,
        use_cuda: bool = False,
    ):
        self.embeddings_model_name = embeddings_model_name

        model_kwargs = {"device": "cuda"} if use_cuda else {"device": "cpu"}

        self.embedding_model: Union[
            HuggingFaceEmbeddings, GoogleGenerativeAIEmbeddings, VertexAIEmbeddings
        ]

        if embeddings_type == "GOOGLE_GENAI":
            self.embedding_model = GoogleGenerativeAIEmbeddings(
                model=self.embeddings_model_name,
                task_type="retrieval_document",
            )
            logging.info("Using Google GenerativeAI embeddings...")

        elif embeddings_type == "GOOGLE_VERTEXAI":
            self.embedding_model = VertexAIEmbeddings(
                model_name=self.embeddings_model_name
            )
            logging.info("Using Google VertexAI embeddings...")

        elif embeddings_type == "HF":
            self.embedding_model = HuggingFaceEmbeddings(
                model_name=self.embeddings_model_name,
                multi_process=False,
                encode_kwargs={"normalize_embeddings": True},
                model_kwargs=model_kwargs,
            )
            logging.info("Using HuggingFace embeddings...")

        else:
            raise ValueError("Invalid embdeddings type specified.")

        self.debug = debug
        self.distance_strategy = distance_strategy

        self.processed_docs: list[Document] = []

        self._faiss_db: Optional[FAISS] = None

    @property
    def faiss_db(self) -> Optional[FAISS]:
        return self._faiss_db

    def _add_to_db(self, documents: list[Document]) -> None:
        if self._faiss_db is None:
            self._faiss_db = FAISS.from_documents(
                documents=documents,
                embedding=self.embedding_model,
                distance_strategy=self.distance_strategy,
            )
        else:
            self._faiss_db.add_documents(documents)

    def add_md_docs(
        self, folder_paths: list[str], chunk_size: int = 500, return_docs: bool = False
    ) -> Optional[list[Document]]:
        logging.info("Processing markdown docs...")
        if not isinstance(folder_paths, list):
            raise ValueError("folder_paths must be a list.")

        processed_mddocs: list[Document] = []

        for folder_path in folder_paths:
            logging.debug(f"Processing [{folder_path}]...")
            processed_mddocs.extend(
                process_md(
                    folder_path=folder_path,
                    chunk_size=chunk_size,
                    split_text=True,
                )
            )

        if processed_mddocs:
            logging.info(f"Adding {folder_paths} to FAISS database...\n")
            self._add_to_db(documents=processed_mddocs)
            self.processed_docs.extend(processed_mddocs)
        else:
            logging.warning("No markdown documents processed.")

        if return_docs:
            return processed_mddocs

        return None

    def add_md_manpages(
        self, folder_paths: list[str], chunk_size: int = 500, return_docs: bool = False
    ) -> Optional[list[Document]]:
        logging.info("Processing markdown manpages...")
        if not isinstance(folder_paths, list):
            raise ValueError("folder_paths must be a list.")

        processed_manpages: list[Document] = []
        for folder_path in folder_paths:
            logging.debug(f"Processing [{folder_path}]...")
            processed_manpages.extend(
                process_md(
                    folder_path=folder_path, split_text=False, chunk_size=chunk_size
                )
            )

        if processed_manpages:
            logging.info(f"Adding {folder_paths} to FAISS database...\n")
            self._add_to_db(documents=processed_manpages)
            self.processed_docs.extend(processed_manpages)
        else:
            logging.warning("No manpages documents processed.")

        if return_docs:
            return processed_manpages

        return None

    def add_html(
        self, folder_paths: list[str], chunk_size: int = 500, return_docs: bool = False
    ) -> Optional[list[Document]]:
        logging.info("Process HTML docs...")
        if not isinstance(folder_paths, list):
            raise ValueError("folder_paths must be a list.")

        processed_html_docs: list[Document] = []
        for folder_path in folder_paths:
            logging.debug(f"Processing [{folder_path}]...")
            processed_html_docs.extend(
                process_html(
                    folder_path=folder_path, split_text=True, chunk_size=chunk_size
                )
            )

        if processed_html_docs:
            logging.info(f"Adding {folder_paths} to FAISS database...\n")
            self._add_to_db(documents=processed_html_docs)
            self.processed_docs.extend(processed_html_docs)
        else:
            logging.warning(f"Could not add {folder_paths}. No HTML docs processed.")

        if return_docs:
            return processed_html_docs

        return None

    def add_documents(
        self, folder_paths: list[str], file_type: str, return_docs: bool = False
    ) -> Optional[list[Document]]:
        logging.info("Processing docs...")
        if not isinstance(folder_paths, list):
            raise ValueError("folder_paths must be a list.")

        processed_otherdocs: list[Document] = []

        for file_path in folder_paths:
            logging.debug(f"Processing [{file_path}]...")
            if file_type == "pdf":
                processed_otherdocs.extend(process_pdf_docs(file_path=file_path))
            else:
                raise ValueError("File type not supported.")

        if processed_otherdocs:
            logging.info(f"Adding [{folder_paths}] to FAISS database...\n")
            self._add_to_db(documents=processed_otherdocs)
            self.processed_docs.extend(processed_otherdocs)
        else:
            logging.warning("No PDF documents processed.")

        if return_docs:
            return processed_otherdocs

        return None

    def get_db_path(self) -> str:
        cur_path = os.path.abspath(__file__)
        path = os.path.join(cur_path, "../../../", "faiss_db")
        path = os.path.abspath(path)  # Ensure proper parent directory
        return path

    def save_db(self, name: str) -> None:
        if self._faiss_db is None:
            raise ValueError("No documents in FAISS database")
        else:
            save_path = f"{self.get_db_path()}/{name}"
            self._faiss_db.save_local(save_path)

    def load_db(self, name: str) -> None:
        load_path = f"{self.get_db_path()}/{name}"
        self._faiss_db = FAISS.load_local(
            load_path, self.embedding_model, allow_dangerous_deserialization=True
        )

    def get_documents(self) -> list[Document]:
        return self._faiss_db.docstore._dict.values()  # type: ignore

    def process_json(self, folder_paths: list[str]) -> FAISS:
        logging.info("Processing json files...")
        if not isinstance(folder_paths, list):
            raise ValueError("folder_paths must be a list.")

        embeddings = self.embedding_model
        json_docs_processed = generate_knowledge_base(folder_paths)
        json_vector_db = FAISS.from_documents(
            json_docs_processed, embeddings, distance_strategy=DistanceStrategy.COSINE
        )
        return json_vector_db

    def get_relevant_documents(self, query: str, k: int = 2) -> str:
        if self._faiss_db is None:
            raise ValueError("No documents in FAISS database")
        retrieved_docs = self._faiss_db.similarity_search(query=query, k=k)
        retrieved_text = ""

        for doc in retrieved_docs:
            retrieved_text += doc.page_content.replace("\n", "") + "\n\n"

        return retrieved_text
