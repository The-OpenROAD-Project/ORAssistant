from .base_chain import BaseChain

from langchain_core.runnables import RunnableParallel, RunnablePassthrough
from langchain.docstore.document import Document

from ..vectorstores.faiss import FAISSVectorDatabase
from langchain_google_vertexai import ChatVertexAI
from langchain_google_genai import ChatGoogleGenerativeAI
from typing import Optional, Tuple, Any, Union


class SimilarityRetrieverChain(BaseChain):
    def __init__(
        self,
        llm_model: Optional[Union[ChatGoogleGenerativeAI, ChatVertexAI]] = None,
        prompt_template_str: Optional[str] = None,
        markdown_docs_path: Optional[list[str]] = None,
        manpages_path: Optional[list[str]] = None,
        html_docs_path: Optional[list[str]] = None,
        other_docs_path: Optional[list[str]] = None,
        embeddings_config: Optional[dict[str, str]] = None,
        use_cuda: bool = False,
        chunk_size: int = 500,
    ):
        super().__init__(
            llm_model=llm_model,
            prompt_template_str=prompt_template_str,
        )

        self.embeddings_config: Optional[dict[str, str]] = embeddings_config
        self.use_cuda: bool = use_cuda

        self.markdown_docs_path: Optional[list[str]] = markdown_docs_path
        self.other_docs_path: Optional[list[str]] = other_docs_path
        self.manpages_path: Optional[list[str]] = manpages_path
        self.html_docs_path: Optional[list[str]] = html_docs_path

        self.chunk_size: int = chunk_size

        self.processed_docs: Optional[list[Document]] = []
        self.processed_manpages: Optional[list[Document]] = []
        self.processed_pdfs: Optional[list[Document]] = []
        self.processed_html: Optional[list[Document]] = []

        self.vector_db: Optional[FAISSVectorDatabase] = None
        self.retriever: Any  # This is Any for now as certain child classes (eg. bm25_retriever_chain) have a different retriever.

    def embed_docs(
        self,
        return_docs: bool = False,
    ) -> Tuple[
        Optional[list[Document]],
        Optional[list[Document]],
        Optional[list[Document]],
        Optional[list[Document]],
    ]:
        if self.vector_db is None:
            self.create_vector_db()

        if self.markdown_docs_path is not None and self.vector_db is not None:
            self.processed_docs = self.vector_db.add_md_docs(
                folder_paths=self.markdown_docs_path,
                chunk_size=self.chunk_size,
                return_docs=return_docs,
            )

        if self.manpages_path is not None and self.vector_db is not None:
            self.processed_manpages = self.vector_db.add_md_manpages(
                folder_paths=self.manpages_path, return_docs=return_docs
            )

        if self.other_docs_path is not None and self.vector_db is not None:
            for other_docs_path in self.other_docs_path:
                if other_docs_path.endswith('.pdf'):
                    self.processed_pdfs = self.vector_db.add_documents(
                        file_paths=[other_docs_path],
                        file_type='pdf',
                        return_docs=return_docs,
                    )
                else:
                    raise ValueError('File type not supported.')

        if self.html_docs_path is not None and self.vector_db is not None:
            self.processed_html = self.vector_db.add_html(
                folder_paths=self.html_docs_path,
                return_docs=return_docs,
            )

        return (
            self.processed_docs,
            self.processed_manpages,
            self.processed_pdfs,
            self.processed_html,
        )

    def create_vector_db(self) -> None:
        if (
            self.embeddings_config is not None
            and self.embeddings_config['name'] is not None
            and self.embeddings_config['type'] is not None
        ):
            self.vector_db = FAISSVectorDatabase(
                embeddings_model_name=self.embeddings_config['name'],
                embeddings_type=self.embeddings_config['type'],
                use_cuda=self.use_cuda,
            )
        else:
            raise ValueError('Embeddings model config not provided correctly.')

    def create_similarity_retriever(self, search_k: Optional[int] = 5) -> None:
        if (
            self.processed_docs == []
            and self.processed_manpages == []
            and self.processed_pdfs == []
            and self.processed_html == []
        ):
            self.embed_docs()

        if self.vector_db is not None and self.vector_db.faiss_db is not None:
            self.retriever = self.vector_db.faiss_db.as_retriever(
                search_type='similarity',
                search_kwargs={'k': search_k},
            )

    def create_llm_chain(self) -> None:
        super().create_llm_chain()

        llm_chain_with_source = RunnableParallel({
            'context': self.retriever,
            'question': RunnablePassthrough(),
        }).assign(answer=self.llm_chain)

        self.llm_chain = llm_chain_with_source

        return
