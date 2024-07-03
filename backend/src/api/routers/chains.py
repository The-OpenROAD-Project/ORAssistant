import os

from fastapi import APIRouter
from pydantic import BaseModel

from ...chains.hybrid_retriever_chain import HybridRetrieverChain
from ...chains.similarity_retriever_chain import SimilarityRetrieverChain
from ...chains.multi_retriever_chain import MultiRetrieverChain

from ...prompts.answer_prompts import summarise_prompt_template

from langchain_google_genai import ChatGoogleGenerativeAI

from dotenv import load_dotenv


class UserInput(BaseModel):
    query: str
    list_sources: bool = False
    list_context: bool = False


load_dotenv()
use_cuda = os.getenv("USE_CUDA")

llm = ChatGoogleGenerativeAI(model="gemini-pro", temperature=1)
hf_embdeddings = "BAAI/bge-large-en-v1.5"
hf_reranker = "BAAI/bge-reranker-base"

router = APIRouter(prefix="/chains", tags=["chains"])

hybrid_retriever = HybridRetrieverChain(
    llm_model=llm,
    prompt_template_str=summarise_prompt_template,
    embeddings_model_name=hf_embdeddings,
    reranking_model_name=hf_reranker,
    contextual_rerank=True,
    use_cuda=use_cuda,
    docs_path=["./data/markdown/ORFS_docs", "./data/markdown/OR_docs"],
    manpages_path=["./data/markdown/manpages"],
)
hybrid_retriever.create_hybrid_retriever()
hybrid_llm_chain = hybrid_retriever.get_llm_chain()

sim_retriever_chain = SimilarityRetrieverChain(
    llm_model=llm,
    prompt_template_str=summarise_prompt_template,
    embeddings_model_name=hf_embdeddings,
    use_cuda=use_cuda,
    docs_path=["./data/markdown/ORFS_docs", "./data/markdown/OR_docs"],
    manpages_path=["./data/markdown/manpages"],
)
sim_retriever_chain.create_similarity_retriever()
sim_llm_chain = sim_retriever_chain.get_llm_chain()

multi_retriever_chain = MultiRetrieverChain(
    llm_model=llm,
    prompt_template_str=summarise_prompt_template,
    embeddings_model_name=hf_embdeddings,
    use_cuda=use_cuda,
    docs_path=["./data/markdown/ORFS_docs", "./data/markdown/OR_docs"],
    manpages_path=["./data/markdown/manpages"],
)
multi_retriever_chain.create_multi_retriever()
multi_llm_chain = multi_retriever_chain.get_llm_chain()


@router.get("/listAll")
async def list_all_chains() -> list:
    return ["/chains/hybrid", "/chains/sim", "/chains/ensemble"]


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

    links = set(links)

    if user_input.list_sources and user_input.list_context:
        response = {
            "response": result["answer"],
            "sources": (links),
            "context": (context),
        }
    elif user_input.list_sources:
        response = {"response": result["answer"], "sources": (links)}
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

    links = list(set(links))

    if user_input.list_sources and user_input.list_context:
        response = {
            "response": result["answer"],
            "sources": (links),
            "context": (context),
        }
    elif user_input.list_sources:
        response = {"response": result["answer"], "sources": (links)}
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

    links = set(links)

    if user_input.list_sources and user_input.list_context:
        response = {
            "response": result["answer"],
            "sources": (links),
            "context": (context),
        }
    elif user_input.list_sources:
        response = {"response": result["answer"], "sources": (links)}
    elif user_input.list_context:
        response = {"response": result["answer"], "context": (context)}
    else:
        response = {"response": result["answer"]}

    return response
