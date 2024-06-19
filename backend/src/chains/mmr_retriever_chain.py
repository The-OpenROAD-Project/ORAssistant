from .similarity_retriever_chain import SimilarityRetrieverChain

from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from ..vectorstores.faiss import FAISSVectorDatabase

from typing import Optional


class MMRRetrieverChain(SimilarityRetrieverChain):
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
            embeddings_model_name=embeddings_model_name,
            use_cuda=use_cuda,
        )

    def create_retriever(
        self,
        vector_db: Optional[FAISSVectorDatabase] = None,
        lambda_mult: Optional[int] = 0.8,
        search_k: Optional[int] = 5,
        chunk_size: Optional[int] = 1000,
        docs_path: Optional[list[str]] = None,
        manpages_path: Optional[list[str]] = None,
    ):
        if vector_db is None:
            super().create_vector_db()
            super().embed_docs(
                docs_path=docs_path,
                manpages_path=manpages_path,
                chunk_size=chunk_size,
                return_docs=False,
            )
        else:
            self.vector_db = vector_db

        self.retriever = self.vector_db.faiss_db.as_retriever(
            search_type="mmr", search_kwargs={"k": search_k, "lambda_mult": lambda_mult}
        )

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

    retriever = MMRRetrieverChain(
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
