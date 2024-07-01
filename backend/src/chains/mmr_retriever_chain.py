from .similarity_retriever_chain import SimilarityRetrieverChain

from langchain_google_genai import ChatGoogleGenerativeAI
from ..vectorstores.faiss import FAISSVectorDatabase

from langchain_core.vectorstores import VectorStoreRetriever

from typing import Optional


class MMRRetrieverChain(SimilarityRetrieverChain):
    def __init__(
        self,
        llm_model: Optional[ChatGoogleGenerativeAI] = None,
        prompt_template_str: Optional[str] = None,
        docs_path: Optional[list[str]] = None,
        manpages_path: Optional[list[str]] = None,
        embeddings_model_name: Optional[str] = None,
        use_cuda: bool = False,
        chunk_size: int = 500,
    ):
        super().__init__(
            llm_model=llm_model,
            prompt_template_str=prompt_template_str,
            embeddings_model_name=embeddings_model_name,
            docs_path=docs_path,
            manpages_path=manpages_path,
            chunk_size=chunk_size,
            use_cuda=use_cuda,
        )

        self.retriever: Optional[VectorStoreRetriever] = None

    def create_mmr_retriever(
        self,
        vector_db: Optional[FAISSVectorDatabase],
        lambda_mult: float = 0.8,
        search_k: int = 5,
    ):
        if vector_db is None:
            super().embed_docs(
                return_docs=False,
            )
        else:
            self.vector_db = vector_db

        if self.vector_db is not None:
            self.retriever = self.vector_db.faiss_db.as_retriever(
                search_type="mmr",
                search_kwargs={"k": search_k, "lambda_mult": lambda_mult},
            )
