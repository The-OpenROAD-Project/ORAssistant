import os
from typing import Optional, Union, Any

from langchain.retrievers import EnsembleRetriever
from langchain.retrievers import ContextualCompressionRetriever
from langchain_core.runnables import RunnableParallel, RunnablePassthrough
from langchain_community.cross_encoders import HuggingFaceCrossEncoder
from langchain_google_vertexai import ChatVertexAI
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_ollama import ChatOllama
from langchain.retrievers.document_compressors.cross_encoder_rerank import (
    CrossEncoderReranker,
)

from .base_chain import BaseChain
from .similarity_retriever_chain import SimilarityRetrieverChain
from .mmr_retriever_chain import MMRRetrieverChain
from .bm25_retriever_chain import BM25RetrieverChain
from ..vectorstores.faiss import FAISSVectorDatabase


class HybridRetrieverChain(BaseChain):
    def __init__(
        self,
        embeddings_config: Optional[dict[str, str]] = None,
        llm_model: Optional[
            Union[ChatGoogleGenerativeAI, ChatVertexAI, ChatOllama]
        ] = None,
        prompt_template_str: Optional[str] = None,
        vector_db: Optional[FAISSVectorDatabase] = None,
        markdown_docs_path: Optional[list[str]] = None,
        manpages_path: Optional[list[str]] = None,
        html_docs_path: Optional[list[str]] = None,
        other_docs_path: Optional[list[str]] = None,
        reranking_model_name: Optional[str] = None,
        use_cuda: bool = False,
        search_k: int = 5,
        weights: list[float] = [0.33, 0.33, 0.33],
        chunk_size: int = 500,
        contextual_rerank: bool = False,
    ):
        super().__init__(
            llm_model=llm_model,
            prompt_template_str=prompt_template_str,
            vector_db=vector_db,
        )
        self.embeddings_config: Optional[dict[str, str]] = embeddings_config

        self.reranking_model_name: Optional[str] = reranking_model_name
        self.use_cuda: bool = use_cuda

        self.search_k: int = search_k
        self.weights: list[float] = weights

        self.markdown_docs_path: Optional[list[str]] = markdown_docs_path
        self.manpages_path: Optional[list[str]] = manpages_path
        self.html_docs_path: Optional[list[str]] = html_docs_path
        self.other_docs_path: Optional[list[str]] = other_docs_path

        self.chunk_size: int = chunk_size

        self.contextual_rerank: bool = contextual_rerank
        self.retriever: Any  # RunnableParallel compatibility

    def create_hybrid_retriever(self) -> None:
        similarity_retriever_chain = SimilarityRetrieverChain(
            llm_model=None,
            prompt_template_str=None,
            vector_db=self.vector_db,
            embeddings_config=self.embeddings_config,
            markdown_docs_path=self.markdown_docs_path,
            manpages_path=self.manpages_path,
            other_docs_path=self.other_docs_path,
            html_docs_path=self.html_docs_path,
            chunk_size=self.chunk_size,
            use_cuda=self.use_cuda,
        )
        if self.vector_db is None:
            path = "./faiss_db"
            load_flag = os.path.isdir(path)  # Checks if database already exists
            if load_flag:
                database_name = similarity_retriever_chain.name
                if database_name in os.listdir(path):
                    similarity_retriever_chain.create_vector_db()
                    similarity_retriever_chain.vector_db.load_db(database_name)
                    self.vector_db = similarity_retriever_chain.vector_db
                    self.vector_db.processed_docs = similarity_retriever_chain.vector_db._faiss_db.docstore._dict.values()
            else:
                similarity_retriever_chain.embed_docs(return_docs=True)
                self.vector_db = similarity_retriever_chain.vector_db

        similarity_retriever_chain.create_similarity_retriever(search_k=self.search_k)
        similarity_retriever = similarity_retriever_chain.retriever

        mmr_retriever_chain = MMRRetrieverChain()
        mmr_retriever_chain.create_mmr_retriever(
            vector_db=self.vector_db, search_k=self.search_k, lambda_mult=0.7
        )
        mmr_retriever = mmr_retriever_chain.retriever

        bm25_retriever_chain = BM25RetrieverChain()

        if self.vector_db is not None and self.vector_db.processed_docs:
            bm25_retriever_chain.create_bm25_retriever(
                embedded_docs=self.vector_db.processed_docs, search_k=self.search_k
            )
            bm25_retriever = bm25_retriever_chain.retriever

        if (
            similarity_retriever is not None
            and mmr_retriever is not None
            and bm25_retriever is not None
        ):
            ensemble_retriever = EnsembleRetriever(
                retrievers=[similarity_retriever, mmr_retriever, bm25_retriever],
                weights=self.weights,
            )

        if self.contextual_rerank:
            compressor = CrossEncoderReranker(
                model=HuggingFaceCrossEncoder(model_name=self.reranking_model_name),
                top_n=self.search_k,
            )
            self.retriever = ContextualCompressionRetriever(
                base_compressor=compressor, base_retriever=ensemble_retriever
            )
        else:
            self.retriever = ensemble_retriever

    def create_llm_chain(self) -> None:
        super().create_llm_chain()

        llm_chain_with_source = RunnableParallel(
            {
                "context": self.retriever,
                "question": RunnablePassthrough(),
            }
        ).assign(answer=self.llm_chain)

        self.llm_chain = llm_chain_with_source

        return
