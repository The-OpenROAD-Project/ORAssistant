from .base_chain import BaseChain
from .similarity_retriever_chain import SimilarityRetrieverChain

from langchain_google_vertexai import ChatVertexAI
from langchain_google_genai import ChatGoogleGenerativeAI

from langchain_core.runnables import RunnableParallel, RunnablePassthrough

from langchain.retrievers import EnsembleRetriever


from typing import Optional, Union


class MultiRetrieverChain(BaseChain):
    def __init__(
        self,
        llm_model: Optional[Union[ChatGoogleGenerativeAI, ChatVertexAI]] = None,
        prompt_template_str: Optional[str] = None,
        markdown_docs_path: Optional[list[str]] = None,
        manpages_path: Optional[list[str]] = None,
        other_docs_path: Optional[list[str]] = None,
        html_docs_path: Optional[list[str]] = None,
        embeddings_config: Optional[dict[str, str]] = None,
        use_cuda: bool = False,
        search_k: list[int] = [5, 5, 5, 5],
        weights: list[float] = [0.25, 0.25, 0.25, 0.25],
        chunk_size: int = 500,
    ):
        super().__init__(
            llm_model=llm_model,
            prompt_template_str=prompt_template_str,
        )
        self.embeddings_config: Optional[dict[str, str]] = embeddings_config
        self.use_cuda: bool = use_cuda

        self.search_k: list[int] = search_k
        self.weights: list[float] = weights

        self.chunk_size: int = chunk_size
        self.markdown_docs_path: Optional[list[str]] = markdown_docs_path
        self.manpages_path: Optional[list[str]] = manpages_path
        self.html_docs_path: Optional[list[str]] = html_docs_path
        self.other_docs_path: Optional[list[str]] = other_docs_path

        self.retriever: Optional[EnsembleRetriever] = None

    def create_multi_retriever(self) -> None:
        docs_similarity_retriever_chain = SimilarityRetrieverChain(
            llm_model=None,
            prompt_template_str=None,
            embeddings_config=self.embeddings_config,
            markdown_docs_path=self.markdown_docs_path,
            chunk_size=self.chunk_size,
        )
        docs_similarity_retriever_chain.embed_docs(return_docs=False)
        docs_similarity_retriever_chain.create_similarity_retriever(
            search_k=self.search_k[0]
        )
        docs_similarity_retriever = docs_similarity_retriever_chain.retriever

        manpages_similarity_retriever_chain = SimilarityRetrieverChain(
            llm_model=None,
            prompt_template_str=None,
            embeddings_config=self.embeddings_config,
            manpages_path=self.manpages_path,
            chunk_size=self.chunk_size,
        )
        manpages_similarity_retriever_chain.embed_docs(return_docs=False)
        manpages_similarity_retriever_chain.create_similarity_retriever(
            search_k=self.search_k[1]
        )
        manpages_similarity_retriever = manpages_similarity_retriever_chain.retriever

        pdfs_similarity_retriever_chain = SimilarityRetrieverChain(
            llm_model=None,
            prompt_template_str=None,
            embeddings_config=self.embeddings_config,
            other_docs_path=self.other_docs_path,
            chunk_size=self.chunk_size,
        )
        pdfs_similarity_retriever_chain.embed_docs(return_docs=False)
        pdfs_similarity_retriever_chain.create_similarity_retriever(
            search_k=self.search_k[2]
        )
        pdfs_similarity_retriever = pdfs_similarity_retriever_chain.retriever

        rtdocs_similarity_retriever_chain = SimilarityRetrieverChain(
            llm_model=None,
            prompt_template_str=None,
            embeddings_config=self.embeddings_config,
            html_docs_path=self.html_docs_path,
            chunk_size=self.chunk_size,
        )
        rtdocs_similarity_retriever_chain.embed_docs(return_docs=False)
        rtdocs_similarity_retriever_chain.create_similarity_retriever(
            search_k=self.search_k[3]
        )
        rtdocs_similarity_retriever = rtdocs_similarity_retriever_chain.retriever

        if (
            docs_similarity_retriever is not None
            and manpages_similarity_retriever is not None
            and pdfs_similarity_retriever is not None
            and rtdocs_similarity_retriever is not None
        ):
            self.retriever = EnsembleRetriever(
                retrievers=[
                    docs_similarity_retriever,
                    manpages_similarity_retriever,
                    pdfs_similarity_retriever,
                    rtdocs_similarity_retriever,
                ],
                weights=self.weights,
            )

    def create_llm_chain(self) -> None:
        super().create_llm_chain()

        llm_chain_with_source = RunnableParallel({
            'context': self.retriever,
            'question': RunnablePassthrough(),
        }).assign(answer=self.llm_chain)  # type: ignore

        self.llm_chain = llm_chain_with_source

        return
