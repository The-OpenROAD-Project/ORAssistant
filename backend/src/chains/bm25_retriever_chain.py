from .similarity_retriever_chain import SimilarityRetrieverChain

from langchain_community.retrievers import BM25Retriever
from langchain_core.vectorstores import VectorStoreRetriever
from langchain.docstore.document import Document
from langchain_google_vertexai import ChatVertexAI
from langchain_google_genai import ChatGoogleGenerativeAI

from typing import Optional, Iterable, Union


class BM25RetrieverChain(SimilarityRetrieverChain):
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
        chunk_size: int = 500,
    ):
        super().__init__(
            llm_model=llm_model,
            prompt_template_str=prompt_template_str,
            embeddings_config=embeddings_config,
            markdown_docs_path=markdown_docs_path,
            manpages_path=manpages_path,
            other_docs_path=other_docs_path,
            html_docs_path=html_docs_path,
            chunk_size=chunk_size,
            use_cuda=use_cuda,
        )

        self.retriever: Optional[Union[VectorStoreRetriever, BM25Retriever]] = None

    def create_bm25_retriever(
        self,
        embedded_docs: Optional[Iterable[Document]],
        search_k: int = 5,
    ) -> None:
        if embedded_docs is None:
            super().create_vector_db()
            (
                processed_docs,
                processed_manpages,
                processed_other_docs,
                processed_rtdocs,
            ) = super().embed_docs(return_docs=True)

            embedded_docs = []
            if processed_docs is not None:
                embedded_docs += processed_docs
            if processed_manpages is not None:
                embedded_docs += processed_manpages
            if processed_other_docs is not None:
                embedded_docs += processed_other_docs
            if processed_rtdocs is not None:
                embedded_docs += processed_rtdocs

        self.retriever = BM25Retriever.from_documents(
            documents=embedded_docs, search_kwargs={'k': search_k}
        )
