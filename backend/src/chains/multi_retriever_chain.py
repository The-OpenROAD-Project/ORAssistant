from .base_chain import BaseChain
from .similarity_retriever_chain import SimilarityRetrieverChain

from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI

from langchain_core.runnables import RunnableParallel, RunnablePassthrough

from langchain.retrievers import EnsembleRetriever
from ..tools.format_docs import format_docs

from ..prompts.answer_prompts import summarise_prompt_template

from typing import Optional


class MultiRetrieverChain(BaseChain):
    def __init__(
        self,
        llm_model: Optional[ChatGoogleGenerativeAI] = None,
        prompt_template_str: Optional[str] = None,
        docs_path: Optional[list[str]] = None,
        manpages_path: Optional[list[str]] = None,
        embeddings_model_name: Optional[str] = None,
        use_cuda: bool = False,
        search_k: list[int] = [5, 5],
        weights: list[float] = [0.5, 0.5],
        chunk_size: int = 500,
    ):
        super().__init__(
            llm_model=llm_model,
            prompt_template_str=prompt_template_str,
        )
        self.embeddings_model_name: Optional[str] = embeddings_model_name
        self.use_cuda: bool = use_cuda

        self.search_k: list[int] = search_k
        self.weights: list[float] = weights

        self.chunk_size: int = chunk_size
        self.docs_path: Optional[list[str]] = docs_path
        self.manpages_path: Optional[list[str]] = manpages_path

        self.retriever: EnsembleRetriever = None

    def create_multi_retriever(
        self,
    ) -> EnsembleRetriever:
        docs_similarity_retriever_chain = SimilarityRetrieverChain(
            llm_model=None,
            prompt_template_str=None,
            embeddings_model_name=self.embeddings_model_name,
            docs_path=self.docs_path,
            chunk_size=self.chunk_size,
        )
        docs_similarity_retriever_chain.embed_docs(return_docs=False)
        docs_similarity_retriever_chain.create_similarity_retriever(search_k=5)
        docs_similarity_retriever = docs_similarity_retriever_chain.retriever

        manpages_similarity_retriever_chain = SimilarityRetrieverChain(
            llm_model=None,
            prompt_template_str=None,
            embeddings_model_name=self.embeddings_model_name,
            manpages_path=self.manpages_path,
            chunk_size=self.chunk_size,
        )
        manpages_similarity_retriever_chain.embed_docs(return_docs=False)
        manpages_similarity_retriever_chain.create_similarity_retriever(search_k=5)
        manpages_similarity_retriever = docs_similarity_retriever_chain.retriever

        if (
            docs_similarity_retriever is not None
            and manpages_similarity_retriever is not None
        ):
            self.retriever = EnsembleRetriever(
                retrievers=[docs_similarity_retriever, manpages_similarity_retriever],
                weights=self.weights,
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

    multi_retriever_chain = MultiRetrieverChain(
        llm_model=llm,
        prompt_template_str=prompt_template_str,
        embeddings_model_name="BAAI/bge-large-en-v1.5",
        use_cuda=True,
        docs_path=["./data/markdown/ORFS_docs", "./data/markdown/OR_docs"],
        manpages_path=["./data/markdown/manpages"],
    )
    multi_retriever_chain.create_multi_retriever()
    llm_chain = multi_retriever_chain.get_llm_chain()

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
