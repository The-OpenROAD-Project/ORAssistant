from .base_chain import BaseChain

from langchain_core.runnables import RunnableParallel, RunnablePassthrough
from langchain_core.vectorstores import VectorStoreRetriever
from langchain.docstore.document import Document as LangchainDocument

from ..vectorstores.faiss import FAISSVectorDatabase
from ..tools.format_docs import format_docs

from langchain_google_genai import ChatGoogleGenerativeAI
from typing import Optional


class SimilarityRetrieverChain(BaseChain):
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
        )

        self.embeddings_model_name = embeddings_model_name
        self.use_cuda = use_cuda

        self.processed_docs = None
        self.processed_manpages = None

        self.vector_db = None
        self.retriever = None

    def embed_docs(
        self,
        docs_path: Optional[list[str]] = None,
        manpages_path: Optional[list[str]] = None,
        chunk_size: Optional[int] = 1000,
        return_docs: Optional[bool] = False,
    ) -> tuple[list[LangchainDocument] | None, list[LangchainDocument] | None]:
        if docs_path is not None:
            self.processed_docs = self.vector_db.process_md_docs(
                folder_paths=docs_path,
                chunk_size=chunk_size,
                return_docs=return_docs,
            )

        if manpages_path is not None:
            self.processed_manpages = self.vector_db.process_md_manpages(
                folder_paths=manpages_path, return_docs=return_docs
            )

        return self.processed_docs, self.processed_manpages

    def create_vector_db(self) -> None:
        self.vector_db = FAISSVectorDatabase(
            embeddings_model_name=self.embeddings_model_name,
            print_progress=True,
            use_cuda=self.use_cuda,
        )
        return

    def get_vector_db(self) -> FAISSVectorDatabase:
        if self.vector_db is None:
            self.create_vector_db()
        return self.vector_db

    def create_retriever(self, search_k: Optional[int] = 5) -> None:
        if self.processed_docs is None and self.processed_manpages is None:
            self.embed_docs()
        self.retriever = self.vector_db.faiss_db.as_retriever(
            search_type="similarity", search_kwargs={"k": search_k}
        )
        return

    def get_retriever(self) -> VectorStoreRetriever:
        if self.retriever is None:
            self.create_retriever()
        return self.retriever

    def create_llm_chain(self) -> None:
        super().create_llm_chain()

        self.create_vector_db()
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
