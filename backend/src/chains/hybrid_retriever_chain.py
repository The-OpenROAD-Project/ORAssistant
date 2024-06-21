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

from typing import Optional


class HybridRetrieverChain(BaseChain):
    def __init__(
        self,
        llm_model: Optional[ChatGoogleGenerativeAI],
        prompt_template_str: Optional[str] = "",
        embeddings_model_name: Optional[str] = "",
        reranking_model_name: Optional[str] = "",
        use_cuda: Optional[bool] = False,
        search_k: Optional[list[int]] = [5, 5, 5],
        weights: Optional[list[int]] = [0.33, 0.33, 0.33],
        chunk_size: Optional[int] = 1000,
        docs_path: Optional[list[str]] = None,
        manpages_path: Optional[list[str]] = None,
        contextual_rerank: Optional[bool] = False,
    ):
        super().__init__(
            llm_model=llm_model,
            prompt_template_str=prompt_template_str,
        )

        self.embeddings_model_name = embeddings_model_name
        self.reranking_model_name = reranking_model_name
        self.use_cuda = use_cuda

        self.search_k = search_k
        self.weights = weights

        self.chunk_size = chunk_size
        self.docs_path = docs_path
        self.manpages_path = manpages_path

        self.contextual_rerank = contextual_rerank

        self.retriever = None

    def create_retriever(self) -> None:
        similarity_retriever_chain = SimilarityRetrieverChain(
            embeddings_model_name=self.embeddings_model_name,
        )
        faiss_db = similarity_retriever_chain.get_vector_db()
        processed_docs, processed_manpages = similarity_retriever_chain.embed_docs(
            docs_path=self.docs_path,
            manpages_path=self.manpages_path,
            chunk_size=self.chunk_size,
            return_docs=True,
        )
        similarity_retriever_chain.create_retriever(search_k=5)
        similarity_retriever = similarity_retriever_chain.get_retriever()

        mmr_retriever_chain = MMRRetrieverChain()
        mmr_retriever_chain.create_retriever(
            vector_db=faiss_db, search_k=5, lambda_mult=0.9
        )
        mmr_retriever = mmr_retriever_chain.get_retriever()

        bm25_retriever_chain = BM25RetrieverChain()
        bm25_retriever_chain.create_retriever(
            embedded_docs=(processed_docs + processed_manpages), search_k=5
        )
        bm25_retriever = bm25_retriever_chain.get_retriever()

        ensemble_retriever = EnsembleRetriever(
            retrievers=[similarity_retriever, mmr_retriever, bm25_retriever],
            weights=[0.33, 0.33, 0.33],
        )

        if self.contextual_rerank is True:
            compressor = CrossEncoderReranker(
                model=HuggingFaceCrossEncoder(model_name=self.reranking_model_name), top_n=5
            )
            self.retriever = ContextualCompressionRetriever(
                base_compressor=compressor, base_retriever=ensemble_retriever
            )
        else:
            self.retriever = ensemble_retriever

        return

    def create_llm_chain(self) -> None:
        super().create_llm_chain()

        self.create_retriever()

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

    prompt_template_str = """
        Use the following context:

        {context}

        -------------------------------------------------------------------------------------------------
        Your task is to act as a knowledgeable assistant for users seeking information and guidance about the OpenROAD project. Avoid speculating or inventing information beyond the scope of the provided data.
        Note that OR refers to OpenROAD and ORFS refers to OpenROAD-Flow-Scripts

        Give a detailed answer to this question: 
        {question}

        """

    retriever = HybridRetrieverChain(
        llm_model=llm,
        prompt_template_str=prompt_template_str,
        embeddings_model_name="BAAI/bge-large-en-v1.5",
        use_cuda=True,
        docs_path=["./data/markdown/ORFS_docs", "./data/markdown/OR_docs"],
        manpages_path=["./data/markdown/manpages"],
        search_k=3,
    )

    retriever_chain = retriever.get_llm_chain()

    while True:
        user_question = input("\n\nAsk a question: ")
        result = retriever_chain.invoke(user_question)

        sources = []
        for i in result["context"]:
            if "url" in i.metadata:
                sources.append(i.metadata["url"])
            elif "source" in i.metadata:
                sources.append(i.metadata["source"])

        sources = set(sources)

        print(result["answer"])

        print("\n\nSources:")
        for i in sources:
            print(i)
