from langchain_community.vectorstores import FAISS
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores.utils import DistanceStrategy
from langchain.docstore.document import Document

from ..tools.process_md import process_md_docs, process_md_manpages
from ..tools.process_json import generate_knowledge_base

from typing import Optional

# from langchain_google_genai import GoogleGenerativeAIEmbeddings
# from langchain_google_vertexai import VertexAIEmbeddings


class FAISSVectorDatabase:
    def __init__(
        self,
        embeddings_model_name: str,
        distance_strategy: DistanceStrategy = DistanceStrategy.COSINE,
        print_progress: bool = False,
        debug: bool = False,
        use_cuda: bool = False,
    ):
        self.embeddings_model_name = embeddings_model_name

        model_kwargs = {"device": "cuda"} if use_cuda else {}
        self.embedding_model = HuggingFaceEmbeddings(
            model_name=self.embeddings_model_name,
            multi_process=False,
            encode_kwargs={"normalize_embeddings": True},
            model_kwargs=model_kwargs,
        )

        # self.embedding_model = GoogleGenerativeAIEmbeddings.model()
        # self.embedding_model = VertexAIEmbeddings(model_name="textembedding-gecko@001")

        self.print_progress = print_progress
        self.debug = debug
        self.distance_strategy = distance_strategy

        self._faiss_db = FAISS.from_documents(
            documents=[Document(page_content="")],
            embedding=self.embedding_model,
            distance_strategy=self.distance_strategy,
        )

    @property
    def faiss_db(self) -> FAISS:
        return self._faiss_db

    def process_md_docs(
        self, folder_paths: list[str], chunk_size: int = 500, return_docs: bool = False
    ) -> Optional[list[Document]]:
        if self.print_progress:
            print("Processing markdown docs...")

        docs_processed = []

        for file_path in folder_paths:
            if self.print_progress:
                print(f"Processing [{file_path}]...")
                docs_processed.extend(
                    process_md_docs(
                        embeddings_model_name=self.embeddings_model_name,
                        files_path=file_path,
                        chunk_size=chunk_size,
                    )
                )

        self._faiss_db.add_documents(docs_processed)

        if return_docs:
            return docs_processed

        return None

    def process_md_manpages(
        self, folder_paths: list[str], return_docs: bool = False
    ) -> Optional[list[Document]]:
        if self.print_progress:
            print("Processing markdown manpages...")

        docs_processed = []

        for file_path in folder_paths:
            if self.print_progress:
                print(f"Processing [{file_path}]...")
                docs_processed.extend(
                    process_md_manpages(
                        files_path=file_path,
                    )
                )

        # Only add if docs were processed
        if docs_processed:
            self._faiss_db.add_documents(docs_processed)

        if return_docs:
            return docs_processed

        return None

    def process_json(self, folder_paths: list[str]) -> FAISS:
        if self.print_progress:
            print("Processing json files...")

        embeddings = self.embedding_model
        json_docs_processed = generate_knowledge_base(folder_paths)
        json_vector_db = FAISS.from_documents(
            json_docs_processed, embeddings, distance_strategy=DistanceStrategy.COSINE
        )
        return json_vector_db

    def get_relevant_documents(self, query: str, k: int = 2) -> str:
        retrieved_docs = self._faiss_db.similarity_search(query=query, k=k)
        retrieved_text = ""

        for doc in retrieved_docs:
            retrieved_text += doc.page_content.replace("\n", "") + "\n\n"

        return retrieved_text
