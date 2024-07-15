from .base_chain import BaseChain
from .similarity_retriever_chain import SimilarityRetrieverChain

from langchain_google_vertexai import ChatVertexAI
from langchain_google_genai import ChatGoogleGenerativeAI

from langchain_core.runnables import RunnableParallel, RunnablePassthrough

from langchain.retrievers import EnsembleRetriever
from ..tools.format_docs import format_docs


from typing import Optional, Union


class MultiRetrieverChain(BaseChain):
    def __init__(
        self,
        llm_model: Optional[Union[ChatGoogleGenerativeAI, ChatVertexAI]] = None,
        prompt_template_str: Optional[str] = None,
        docs_path: Optional[list[str]] = None,
        manpages_path: Optional[list[str]] = None,
        embeddings_model_name: str = 'BAAI/bge-large-en-v1.5',
        use_cuda: bool = False,
        search_k: list[int] = [5, 5],
        weights: list[float] = [0.5, 0.5],
        chunk_size: int = 500,
    ):
        super().__init__(
            llm_model=llm_model,
            prompt_template_str=prompt_template_str,
        )
        self.embeddings_model_name: str = embeddings_model_name
        self.use_cuda: bool = use_cuda

        self.search_k: list[int] = search_k
        self.weights: list[float] = weights

        self.chunk_size: int = chunk_size
        self.docs_path: Optional[list[str]] = docs_path
        self.manpages_path: Optional[list[str]] = manpages_path

        self.retriever: Optional[EnsembleRetriever] = None

    def create_multi_retriever(self) -> None:
        docs_similarity_retriever_chain = SimilarityRetrieverChain(
            llm_model=None,
            prompt_template_str=None,
            embeddings_model_name=self.embeddings_model_name,
            docs_path=self.docs_path,
            chunk_size=self.chunk_size,
        )
        docs_similarity_retriever_chain.embed_docs(return_docs=False)
        docs_similarity_retriever_chain.create_similarity_retriever(search_k=5)
        docs_similarity_retriever = docs_similarity_retriever_chain.retriever

        manpages_similarity_retriever_chain = SimilarityRetrieverChain(
            llm_model=None,
            prompt_template_str=None,
            embeddings_model_name=self.embeddings_model_name,
            manpages_path=self.manpages_path,
            chunk_size=self.chunk_size,
        )
        manpages_similarity_retriever_chain.embed_docs(return_docs=False)
        manpages_similarity_retriever_chain.create_similarity_retriever(search_k=5)
        manpages_similarity_retriever = docs_similarity_retriever_chain.retriever

        if (
            docs_similarity_retriever is not None
            and manpages_similarity_retriever is not None
        ):
            self.retriever = EnsembleRetriever(
                retrievers=[docs_similarity_retriever, manpages_similarity_retriever],
                weights=self.weights,
            )

    def create_llm_chain(self) -> None:
        super().create_llm_chain()

        self.llm_chain = (
            RunnablePassthrough.assign(context=(lambda x: format_docs(x['context'])))
            | self.llm_chain
        )

        llm_chain_with_source = RunnableParallel({
            'context': self.retriever,
            'question': RunnablePassthrough(),
        }).assign(answer=self.llm_chain)  # type: ignore

        self.llm_chain = llm_chain_with_source

        return
