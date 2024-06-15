from langchain_community.vectorstores import FAISS
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores.utils import DistanceStrategy

from .tools.process_md import chunk_markdown
from .tools.process_json import generate_knowledge_base

from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_google_vertexai import VertexAIEmbeddings

from typing import Union


class FAISSVectorDatabase:
    def __init__(
        self,
        embeddings_model_name: str,
        print_progress: bool = False,
        debug: bool = False,
        use_cuda: bool = False,
    ):
        self.embeddings_model_name = embeddings_model_name
        if use_cuda:
            self.embedding_model = HuggingFaceEmbeddings(
                model_name=self.embeddings_model_name,
                multi_process=False,
                encode_kwargs={"normalize_embeddings": True},
                model_kwargs={"device": "cuda"},
            )
        else:
            self.embedding_model = HuggingFaceEmbeddings(
                model_name=self.embeddings_model_name,
                multi_process=False,
                encode_kwargs={"normalize_embeddings": True},
            )

        # self.embedding_model = GoogleGenerativeAIEmbeddings.model()
        # self.embedding_model = VertexAIEmbeddings(model_name="textembedding-gecko@001")
        self.print_progress = print_progress
        self.debug = debug

    def process_md(
        self, folder_paths: list[str], chunk_size: int = 1000, return_docs: bool = False
    ) -> Union[FAISS, tuple[FAISS, list]]:
        if self.print_progress is True:
            print("Processing markdown files...")

        docs_processed = []

        for file_path in folder_paths:
            if self.print_progress is True:
                print(f"Processing [{file_path}]...")
                docs_processed.extend(chunk_markdown(
                    embeddings_model_name=self.embeddings_model_name,
                    files_path=file_path,
                    chunk_size=chunk_size,
                ))

        md_vector_db = FAISS.from_documents(
            documents=docs_processed,
            embedding=self.embedding_model,
            distance_strategy=DistanceStrategy.COSINE,
        )

        if return_docs:
            return md_vector_db, docs_processed
        else:
            return md_vector_db

    def process_json(self, folder_paths: list[str]) -> FAISS:
        if self.print_progress is True:
            print("Processing json files...")

        embeddings = self.embedding_model
        json_docs_processed = generate_knowledge_base(folder_paths)
        json_vector_db = FAISS.from_documents(
            json_docs_processed, embeddings, distance_strategy=DistanceStrategy.COSINE
        )
        return json_vector_db

    def get_relevant_documents(self, query: str, k1: int = 2, k2: int = 4) -> str:
        retrieved_docs = self.md_vector_db.similarity_search_(query=query, k=k1)
        retrieved_text = ""

        for doc in retrieved_docs:
            retrieved_text += doc.page_content.replace("\n", "") + "\n\n"

        retrieved_json_docs = self.json_vector_db.similarity_search(query=query, k=k2)
        for doc in retrieved_json_docs:
            retrieved_text += doc.page_content + "\n\n"

        if self.debug is True:
            print("Retrieved text: ", retrieved_text)
            print()

        return retrieved_text
