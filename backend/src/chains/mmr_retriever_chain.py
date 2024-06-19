from .similarity_retriever_chain import SimilarityRetrieverChain

from langchain_google_genai import ChatGoogleGenerativeAI
from ..vectorstores.faiss import FAISSVectorDatabase

from typing import Optional


class MMRRetrieverChain(SimilarityRetrieverChain):
    def __init__(
        self,
        llm_model: Optional[ChatGoogleGenerativeAI] = None,
        prompt_template_str: Optional[str] = "",
        embeddings_model_name: Optional[str] = "",
        use_cuda: Optional[bool] = False,
    ):
        super().__init__(
            llm_model=llm_model,
            prompt_template_str=prompt_template_str,
            embeddings_model_name=embeddings_model_name,
            use_cuda=use_cuda,
        )

    def create_retriever(
        self,
        vector_db: Optional[FAISSVectorDatabase] = None,
        lambda_mult: Optional[int] = 0.8,
        search_k: Optional[int] = 5,
        chunk_size: Optional[int] = 1000,
        docs_path: Optional[list[str]] = None,
        manpages_path: Optional[list[str]] = None,
    ) -> None:
        if vector_db is None:
            super().create_vector_db()
            super().embed_docs(
                docs_path=docs_path,
                manpages_path=manpages_path,
                chunk_size=chunk_size,
                return_docs=False,
            )
        else:
            self.vector_db = vector_db

        self.retriever = self.vector_db.faiss_db.as_retriever(
            search_type="mmr", search_kwargs={"k": search_k, "lambda_mult": lambda_mult}
        )

        return
