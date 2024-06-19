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
        llm_model,
        prompt_template_str,
        embeddings_model_name,
        use_cuda: bool = False,
        search_k: int = 5,
        docs_path: Optional[list[str]] = None,
        manpages_path : Optional[list[str]] = None,
    ):
        super().__init__(llm_model=llm_model, prompt_template_str=prompt_template_str)

        self.vector_db = FAISSVectorDatabase(
            embeddings_model_name=embeddings_model_name,
            print_progress=True,
            use_cuda=use_cuda,
        )
        self.docs_path = docs_path
        self.manpages_path = manpages_path
        self.search_k = search_k

        self.similarity_retriever = None

    def _create_retriever(self):
        if self.docs_path is not None:
            self.vector_db.process_md_docs(
                folder_paths=self.docs_path,
                chunk_size=2000,
                return_docs=True,
            )

        if self.manpages_path is not None:
            self.vector_db.process_md_manpages(
                folder_paths=self.manpages_path, return_docs=True
            )

        self.similarity_retriever = self.vector_db.faiss_db.as_retriever(
            search_type="similarity", search_kwargs={"k": self.search_k}
        )

        return

    def create_llm_chain(self):
        super().create_llm_chain()
        self._create_retriever()

        self.llm_chain = (
            RunnablePassthrough.assign(context=(lambda x: format_docs(x["context"])))
            | self.llm_chain
        )

        llm_chain_with_source = RunnableParallel({
            "context": self.similarity_retriever,
            "question": RunnablePassthrough(),  
        }).assign(answer=self.llm_chain)

        self.llm_chain = llm_chain_with_source

        return

    def get_retriever(self):
        if self.similarity_retriever is None:
            self._create_retriever()
        return self.similarity_retriever


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

    similarity_retriever = SimilarityRetrieverChain(
        llm_model=llm,
        prompt_template_str=prompt_template_str,
        embeddings_model_name="BAAI/bge-large-en-v1.5",
        use_cuda=True,
        docs_path=["./data/markdown/ORFS_docs", "./data/markdown/OR_docs"],
        manpages_path=["./data/markdown/manpages"],
        search_k=3,
    )

    similarity_retriever_chain = similarity_retriever.get_llm_chain()

    while True:
        user_question = input("\n\nAsk a question: ")
        result = similarity_retriever_chain.invoke(user_question)

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

