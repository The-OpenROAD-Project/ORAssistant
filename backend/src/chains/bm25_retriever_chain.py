from .similarity_retriever_chain import SimilarityRetrieverChain

from langchain_community.retrievers import BM25Retriever
from langchain_core.vectorstores import VectorStoreRetriever
from langchain.docstore.document import Document

from langchain_google_genai import ChatGoogleGenerativeAI

from typing import Optional, Iterable, Union


class BM25RetrieverChain(SimilarityRetrieverChain):
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

        self.retriever: Optional[Union[VectorStoreRetriever, BM25Retriever]] = None

    def create_bm25_retriever(
        self,
        embedded_docs: Optional[Iterable[Document]],
        search_k: int = 5,
    ):
        if embedded_docs is None:
            super().create_vector_db()
            processed_docs, processed_manpages = super().embed_docs(return_docs=True)

            embedded_docs = []
            if processed_docs is not None:
                embedded_docs += processed_docs
            if processed_manpages is not None:
                embedded_docs += processed_manpages

        self.retriever = BM25Retriever.from_documents(
            documents=embedded_docs, search_kwargs={"k": search_k}
        )
