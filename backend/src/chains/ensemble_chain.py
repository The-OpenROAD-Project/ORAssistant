from dotenv import load_dotenv

from langchain.prompts import ChatPromptTemplate
from langchain_google_genai import ChatGoogleGenerativeAI

from langchain.retrievers import EnsembleRetriever
from langchain_community.retrievers import BM25Retriever

from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough, RunnableParallel

from ..vectorstores.faiss import FAISSVectorDatabase
from ..tools.format_docs import format_docs

from langchain_google_vertexai import ChatVertexAI

load_dotenv()

llm = ChatGoogleGenerativeAI(model="gemini-pro", temperature=1)
# llm = ChatVertexAI(model_name="gemini-1.5-pro")

vector_db = FAISSVectorDatabase(
    embeddings_model_name="BAAI/bge-large-en-v1.5", print_progress=True, use_cuda=True
)

prompt_template_str = """
Use the following context:

{context}

-------------------------------------------------------------------------------------------------
Your task is to act as a knowledgeable assistant for users seeking information and guidance about the OpenROAD project. Avoid speculating or inventing information beyond the scope of the provided data.
Note that OR refers to OpenROAD and ORFS refers to OpenROAD-Flow-Scripts

Give a detailed answer to this question: 
{question}

"""

prompt_template = ChatPromptTemplate.from_template(prompt_template_str)

docs_processed = vector_db.process_md_docs(
    folder_paths=["./data/markdown/OR_docs", "./data/markdown/ORFS_docs"],
    chunk_size=1000,
    return_docs=True,
)

manpages_processed = vector_db.process_md_manpages(
    folder_paths=["./data/markdown/manpages"],
    return_docs=True
)

bm25_docs = docs_processed + manpages_processed

faiss_vector_db = vector_db.get_db

k = [5, 2, 1]

similarity_retriever = faiss_vector_db.as_retriever(
    search_type="similarity", search_kwargs={"k": k[0]}
)
mmr_retriever = faiss_vector_db.as_retriever(
    search_type="mmr", search_kwargs={"k": k[1],"lambda_mult":0.9}
)
bm25_retriever = BM25Retriever.from_documents(
    documents=bm25_docs, search_kwargs={"k": k[2]}
)

ensemble_retriever = EnsembleRetriever(
    retrievers=[similarity_retriever, mmr_retriever, bm25_retriever],
    weights=[0.7, 0.2, 0.1],
)

output_parser = StrOutputParser()

llm_chain = (
    RunnablePassthrough.assign(context=(lambda x: format_docs(x["context"])))
    | prompt_template
    | llm
    | output_parser
)

llm_chain_with_source = RunnableParallel({
    "context": ensemble_retriever,
    "question": RunnablePassthrough(),
}).assign(answer=llm_chain)

if __name__ == "__main__":
    while True:
        links = []
        user_question = input("\n\nAsk a question: ")
        result = llm_chain_with_source.invoke(user_question)

        for i in result["context"]:
            if i.metadate["url"] is not None:
                links.append(i.metadata["url"])

        links = set(links)

        print(result["answer"])

        print("\n\nSources:")
        for i in links:
            print(i)
