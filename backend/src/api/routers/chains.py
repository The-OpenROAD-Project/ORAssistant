from fastapi import APIRouter
from pydantic import BaseModel

from ...chains.hybrid_retriever_chain import HybridRetrieverChain
from ...chains.similarity_retriever_chain import SimilarityRetrieverChain
from ...chains.multi_retriever_chain import MultiRetrieverChain

from langchain_google_genai import ChatGoogleGenerativeAI

from dotenv import load_dotenv


class UserInput(BaseModel):
    query: str
    list_sources: bool = False
    list_context: bool = False


load_dotenv()


llm = ChatGoogleGenerativeAI(model="gemini-pro", temperature=1)


router = APIRouter(prefix="/chains", tags=["chains"])

prompt_template_str = """
    Use the following context:

    {context}

    -------------------------------------------------------------------------------------------------
    Your task is to act as a knowledgeable assistant for users seeking information and guidance about the OpenROAD project. Avoid speculating or inventing information beyond the scope of the provided data.
    Note that OR refers to OpenROAD and ORFS refers to OpenROAD-Flow-Scripts

    Give a detailed answer to this question: 
    {question}

    """

hybrid_retriever = HybridRetrieverChain(
    llm_model=llm,
    prompt_template_str=prompt_template_str,
    embeddings_model_name="BAAI/bge-large-en-v1.5",
    reranking_model_name="BAAI/bge-reranker-base",
    contextual_rerank=True,
    use_cuda=True,
    docs_path=["./data/markdown/ORFS_docs", "./data/markdown/OR_docs"],
    manpages_path=["./data/markdown/manpages"],
)
hybrid_retriever.create_hybrid_retriever()
hybrid_llm_chain = hybrid_retriever.get_llm_chain()

sim_retriever_chain = SimilarityRetrieverChain(
    llm_model=llm,
    prompt_template_str=prompt_template_str,
    embeddings_model_name="BAAI/bge-large-en-v1.5",
    use_cuda=True,
    docs_path=["./data/markdown/ORFS_docs", "./data/markdown/OR_docs"],
    manpages_path=["./data/markdown/manpages"],
)
sim_retriever_chain.create_similarity_retriever()
sim_llm_chain = sim_retriever_chain.get_llm_chain()

multi_retriever_chain = MultiRetrieverChain(
    llm_model=llm,
    prompt_template_str=prompt_template_str,
    embeddings_model_name="BAAI/bge-large-en-v1.5",
    use_cuda=True,
    docs_path=["./data/markdown/ORFS_docs", "./data/markdown/OR_docs"],
    manpages_path=["./data/markdown/manpages"],
)
multi_retriever_chain.create_multi_retriever()
multi_llm_chain = multi_retriever_chain.get_llm_chain()



@router.post("/hybrid")
async def get_hybrid_response(user_input: UserInput) -> dict:
    user_question = user_input.query
    result = hybrid_llm_chain.invoke(user_question)

    links = []
    context = []
    for i in result["context"]:
        if "url" in i.metadata:
            links.append(i.metadata["url"])
        elif "source" in i.metadata:
            links.append(i.metadata["source"])
        context.append(i.page_content)

    links_set = set(links)

    if user_input.list_sources and user_input.list_context:
        response = {
            "response": result["answer"],
            "sources": (links_set),
            "context": (context),
        }
    elif user_input.list_sources:
        response = {"response": result["answer"], "sources": (links_set)}
    elif user_input.list_context:
        response = {"response": result["answer"], "context": (context)}
    else:
        response = {"response": result["answer"]}

    return response

@router.post("/sim")
async def get_sim_response(user_input: UserInput) -> dict:
    user_question = user_input.query
    result = hybrid_llm_chain.invoke(user_question)

    links = []
    context = []
    for i in result["context"]:
        if "url" in i.metadata:
            links.append(i.metadata["url"])
        elif "source" in i.metadata:
            links.append(i.metadata["source"])
        context.append(i.page_content)

    links_set = set(links)

    if user_input.list_sources and user_input.list_context:
        response = {
            "response": result["answer"],
            "sources": (links_set),
            "context": (context),
        }
    elif user_input.list_sources:
        response = {"response": result["answer"], "sources": (links_set)}
    elif user_input.list_context:
        response = {"response": result["answer"], "context": (context)}
    else:
        response = {"response": result["answer"]}

    return response

@router.post("/ensemble")
async def get_response(user_input: UserInput) -> dict:
    user_question = user_input.query
    result = hybrid_llm_chain.invoke(user_question)

    links = []
    context = []
    for i in result["context"]:
        if "url" in i.metadata:
            links.append(i.metadata["url"])
        elif "source" in i.metadata:
            links.append(i.metadata["source"])
        context.append(i.page_content)

    links_set = set(links)

    if user_input.list_sources and user_input.list_context:
        response = {
            "response": result["answer"],
            "sources": (links_set),
            "context": (context),
        }
    elif user_input.list_sources:
        response = {"response": result["answer"], "sources": (links_set)}
    elif user_input.list_context:
        response = {"response": result["answer"], "context": (context)}
    else:
        response = {"response": result["answer"]}

    return response
