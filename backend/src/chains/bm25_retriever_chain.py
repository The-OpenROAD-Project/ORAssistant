from .similarity_retriever_chain import SimilarityRetrieverChain

from langchain_community.retrievers import BM25Retriever
from langchain.docstore.document import Document as LangchainDocument

from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI

from typing import Optional


class BM25RetrieverChain(SimilarityRetrieverChain):
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
        embedded_docs: Optional[list[LangchainDocument]] = None,
        search_k: Optional[int] = 5,
        chunk_size: Optional[int] = 1000,
        docs_path: Optional[list[str]] = None,
        manpages_path: Optional[list[str]] = None,
    ):
        if embedded_docs is None:
            super().create_vector_db()
            processed_docs, manpages_processed = (
                super()
                .super()
                .embed_docs(
                    docs_path=docs_path,
                    manpages_path=manpages_path,
                    chunk_size=chunk_size,
                    return_docs=True,
                )
            )
            embedded_docs = processed_docs + manpages_processed

        self.retriever = BM25Retriever.from_documents(
            documents=embedded_docs, search_kwargs={"k": search_k}
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

    retriever = BM25RetrieverChain(
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
