from .base_chain import BaseChain

from langchain_core.runnables import RunnableParallel, RunnablePassthrough
from langchain.docstore.document import Document

from ..vectorstores.faiss import FAISSVectorDatabase
from ..tools.format_docs import format_docs
from langchain_google_vertexai import ChatVertexAI
from langchain_google_genai import ChatGoogleGenerativeAI
from typing import Optional, Tuple, Any, Union


from ..prompts.answer_prompts import summarise_prompt_template


from dotenv import load_dotenv


class SimilarityRetrieverChain(BaseChain):
    def __init__(
        self,
        llm_model: Optional[Union[ChatGoogleGenerativeAI, ChatVertexAI]] = None,
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
        )

        self.embeddings_model_name: Optional[str] = embeddings_model_name
        self.use_cuda: bool = use_cuda

        self.docs_path: Optional[list[str]] = docs_path
        self.manpages_path: Optional[list[str]] = manpages_path
        self.chunk_size: int = chunk_size

        self.processed_docs: Optional[list[Document]] = []
        self.processed_manpages: Optional[list[Document]] = []

        self.vector_db: Optional[FAISSVectorDatabase] = None
        self.retriever: Any  # This is Any for now as certain child classes (eg. bm25_retriever_chain) have a different retriever.

    def embed_docs(
        self,
        return_docs: bool = False,
    ) -> Tuple[Optional[list[Document]], Optional[list[Document]]]:
        if self.vector_db is None:
            self.create_vector_db()

        if self.docs_path is not None and self.vector_db is not None:
            self.processed_docs = self.vector_db.process_md_docs(
                folder_paths=self.docs_path,
                chunk_size=self.chunk_size,
                return_docs=return_docs,
            )

        if self.manpages_path is not None and self.vector_db is not None:
            self.processed_manpages = self.vector_db.process_md_manpages(
                folder_paths=self.manpages_path, return_docs=return_docs
            )

        return self.processed_docs, self.processed_manpages

    def create_vector_db(self):
        self.vector_db = FAISSVectorDatabase(
            embeddings_model_name=self.embeddings_model_name,
            print_progress=True,
            use_cuda=self.use_cuda,
        )

    def create_similarity_retriever(self, search_k: Optional[int] = 5):
        if self.processed_docs == [] and self.processed_manpages == []:
            self.embed_docs()

        if self.vector_db is not None:
            self.retriever = self.vector_db.faiss_db.as_retriever(
                search_type="similarity",
                search_kwargs={"k": search_k},
            )

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

    sim_retriever_chain = SimilarityRetrieverChain(
        llm_model=llm,
        prompt_template_str=prompt_template_str,
        embeddings_model_name="BAAI/bge-large-en-v1.5",
        use_cuda=True,
        docs_path=["./data/markdown/ORFS_docs", "./data/markdown/OR_docs"],
        manpages_path=["./data/markdown/manpages"],
    )
    sim_retriever_chain.create_similarity_retriever()
    llm_chain = sim_retriever_chain.get_llm_chain()

    while True:
        user_question = input("\n\nAsk a question: ")
        result = llm_chain.invoke(user_question)

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
