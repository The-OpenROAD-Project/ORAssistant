from .base_chain import BaseChain

from langchain_core.runnables import RunnableParallel, RunnablePassthrough


from ..vectorstores.faiss import FAISSVectorDatabase
from ..tools.format_docs import format_docs

from dotenv import load_dotenv
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
    ):
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

    def create_vector_db(self):
        self.vector_db = FAISSVectorDatabase(
            embeddings_model_name=self.embeddings_model_name,
            print_progress=True,
            use_cuda=self.use_cuda,
        )

    def get_vector_db(self):
        if self.vector_db is None:
            self.create_vector_db()
        return self.vector_db

    def create_retriever(self, search_k: Optional[int] = 5):
        if self.processed_docs is None and self.processed_manpages is None:
            self.embed_docs()
        self.retriever = self.vector_db.faiss_db.as_retriever(
            search_type="similarity", search_kwargs={"k": search_k}
        )
        return

    def get_retriever(self):
        if self.retriever is None:
            self.create_retriever()
        return self.retriever

    def create_llm_chain(self):
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


if __name__ == "__main__":
    load_dotenv()
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

    retriever = SimilarityRetrieverChain(
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
