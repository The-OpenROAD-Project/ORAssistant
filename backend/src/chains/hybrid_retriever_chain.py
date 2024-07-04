from .base_chain import BaseChain
from .similarity_retriever_chain import SimilarityRetrieverChain
from .mmr_retriever_chain import MMRRetrieverChain
from .bm25_retriever_chain import BM25RetrieverChain

from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI

from langchain_core.runnables import RunnableParallel, RunnablePassthrough

from langchain.retrievers import EnsembleRetriever
from ..tools.format_docs import format_docs

from langchain.retrievers import ContextualCompressionRetriever
from langchain.retrievers.document_compressors import CrossEncoderReranker
from langchain_community.cross_encoders import HuggingFaceCrossEncoder

from ..prompts.answer_prompts import summarise_prompt_template

from typing import Optional, Union


class HybridRetrieverChain(BaseChain):
    def __init__(
        self,
        llm_model: Optional[ChatGoogleGenerativeAI] = None,
        prompt_template_str: Optional[str] = None,
        docs_path: Optional[list[str]] = None,
        manpages_path: Optional[list[str]] = None,
        embeddings_model_name: Optional[str] = None,
        reranking_model_name: Optional[str] = None,
        use_cuda: bool = False,
        search_k: list[int] = [5, 5, 5],
        weights: list[float] = [0.33, 0.33, 0.33],
        chunk_size: int = 500,
        contextual_rerank: bool = False,
    ):
        super().__init__(
            llm_model=llm_model,
            prompt_template_str=prompt_template_str,
        )
        self.embeddings_model_name: Optional[str] = embeddings_model_name
        self.reranking_model_name: Optional[str] = reranking_model_name
        self.use_cuda: bool = use_cuda

        self.search_k: list[int] = search_k
        self.weights: list[float] = weights

        self.chunk_size: int = chunk_size
        self.docs_path: Optional[list[str]] = docs_path
        self.manpages_path: Optional[list[str]] = manpages_path

        self.contextual_rerank: bool = contextual_rerank
        self.retriever: Optional[
            Union[EnsembleRetriever, ContextualCompressionRetriever]
        ] = None

    def create_hybrid_retriever(
        self,
    ):
        similarity_retriever_chain = SimilarityRetrieverChain(
            llm_model=None,
            prompt_template_str=None,
            embeddings_model_name=self.embeddings_model_name,
            docs_path=self.docs_path,
            manpages_path=self.manpages_path,
            chunk_size=self.chunk_size,
        )

        processed_docs, processed_manpages = similarity_retriever_chain.embed_docs(
            return_docs=True
        )
        faiss_db = similarity_retriever_chain.vector_db
        similarity_retriever_chain.create_similarity_retriever(search_k=5)
        similarity_retriever = similarity_retriever_chain.retriever

        mmr_retriever_chain = MMRRetrieverChain()
        mmr_retriever_chain.create_mmr_retriever(
            vector_db=faiss_db, search_k=5, lambda_mult=0.9
        )
        mmr_retriever = mmr_retriever_chain.retriever

        embedded_docs = []
        if processed_docs is not None:
            embedded_docs += processed_docs
        if processed_manpages is not None:
            embedded_docs += processed_manpages

        bm25_retriever_chain = BM25RetrieverChain()
        bm25_retriever_chain.create_bm25_retriever(
            embedded_docs=embedded_docs, search_k=5
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
                top_n=5,
            )
            self.retriever = ContextualCompressionRetriever(
                base_compressor=compressor, base_retriever=ensemble_retriever
            )
        else:
            self.retriever = ensemble_retriever

    def create_llm_chain(self) -> None:
        super().create_llm_chain()

        self.llm_chain = (
            RunnablePassthrough.assign(context=(lambda x: format_docs(x["context"])))
            | self.llm_chain
        )

        llm_chain_with_source = RunnableParallel({
            "context": self.retriever,
            "question": RunnablePassthrough(),
        }).assign(answer=self.llm_chain)

        self.llm_chain = llm_chain_with_source

        return


if __name__ == "__main__":
    load_dotenv()

    # from langchain_google_vertexai import ChatVertexAI
    # llm = ChatVertexAI(model_name="gemini-1.5-pro")

    llm = ChatGoogleGenerativeAI(model="gemini-pro", temperature=1)

    prompt_template_str = summarise_prompt_template

    hybrid_retriever_chain = HybridRetrieverChain(
        llm_model=llm,
        prompt_template_str=prompt_template_str,
        embeddings_model_name="BAAI/bge-large-en-v1.5",
        reranking_model_name="BAAI/bge-reranker-base",
        use_cuda=True,
        docs_path=["./data/markdown/ORFS_docs", "./data/markdown/OR_docs"],
        manpages_path=["./data/markdown/manpages"],
    )
    hybrid_retriever_chain.create_hybrid_retriever()
    retriever_chain = hybrid_retriever_chain.get_llm_chain()

    while True:
        user_question = input("\n\nAsk a question: ")
        result = retriever_chain.invoke(user_question)

        sources = []
        for i in result["context"]:
            if "url" in i.metadata:
                sources.append(i.metadata["url"])
            elif "source" in i.metadata:
                sources.append(i.metadata["source"])

        print(result["answer"])

        print("\n\nSources:")
        for i in set(sources):
            print(i)
