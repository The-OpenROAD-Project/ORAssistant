from .base_chain import BaseChain
from .similarity_retriever_chain import SimilarityRetrieverChain
from .mmr_retriever_chain import MMRRetrieverChain
from .bm25_retriever_chain import BM25RetrieverChain


from langchain.retrievers import EnsembleRetriever
from langchain.retrievers import ContextualCompressionRetriever
from langchain.retrievers.document_compressors.cross_encoder_rerank import (
    CrossEncoderReranker,
)

from langchain_core.runnables import RunnableParallel, RunnablePassthrough
from langchain_community.cross_encoders import HuggingFaceCrossEncoder
from langchain_google_vertexai import ChatVertexAI
from langchain_google_genai import ChatGoogleGenerativeAI

from typing import Optional, Union


class HybridRetrieverChain(BaseChain):
    def __init__(
        self,
        embeddings_config: Optional[dict[str, str]] = None,
        llm_model: Optional[Union[ChatGoogleGenerativeAI, ChatVertexAI]] = None,
        prompt_template_str: Optional[str] = None,
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
        self.retriever: Optional[
            Union[EnsembleRetriever, ContextualCompressionRetriever]
        ] = None

    def create_hybrid_retriever(self) -> None:
        similarity_retriever_chain = SimilarityRetrieverChain(
            llm_model=None,
            prompt_template_str=None,
            embeddings_config=self.embeddings_config,
            markdown_docs_path=self.markdown_docs_path,
            manpages_path=self.manpages_path,
            other_docs_path=self.other_docs_path,
            html_docs_path=self.html_docs_path,
            chunk_size=self.chunk_size,
        )

        processed_docs, processed_manpages, processed_pdfs, processed_rtdocs = (
            similarity_retriever_chain.embed_docs(return_docs=True)
        )
        faiss_db = similarity_retriever_chain.vector_db
        similarity_retriever_chain.create_similarity_retriever(search_k=10)
        similarity_retriever = similarity_retriever_chain.retriever

        mmr_retriever_chain = MMRRetrieverChain()
        mmr_retriever_chain.create_mmr_retriever(
            vector_db=faiss_db, search_k=10, lambda_mult=0.7
        )
        mmr_retriever = mmr_retriever_chain.retriever

        embedded_docs = []
        if processed_docs is not None:
            embedded_docs += processed_docs
        if processed_manpages is not None:
            embedded_docs += processed_manpages
        if processed_pdfs is not None:
            embedded_docs += processed_pdfs
        if processed_rtdocs is not None:
            embedded_docs += processed_rtdocs

        bm25_retriever_chain = BM25RetrieverChain()
        bm25_retriever_chain.create_bm25_retriever(
            embedded_docs=embedded_docs, search_k=10
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

        llm_chain_with_source = RunnableParallel({
            'context': self.retriever,
            'question': RunnablePassthrough(),
        }).assign(answer=self.llm_chain)  # type: ignore

        self.llm_chain = llm_chain_with_source

        return
