import os
from typing import Any
from fastapi import APIRouter
from dotenv import load_dotenv
from typing import Union

from langchain_google_vertexai import ChatVertexAI
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_ollama import ChatOllama

from ...chains.hybrid_retriever_chain import HybridRetrieverChain
from ...chains.similarity_retriever_chain import SimilarityRetrieverChain
from ...prompts.prompt_templates import summarise_prompt_template
from ..models.response_model import ChatResponse, UserInput, ContextSource

load_dotenv()

required_env_vars = [
    "USE_CUDA",
    "LLM_TEMP",
    "HF_EMBEDDINGS",
    "HF_RERANKER",
    "GOOGLE_GEMINI",
]

if any(os.getenv(var) is None for var in required_env_vars):
    raise ValueError("One or more environment variables are not set.")

use_cuda: bool = False
llm_temp: float = 0.0

if str(os.getenv("USE_CUDA")).lower() in ("true"):
    use_cuda = True

llm_temp_str = os.getenv("LLM_TEMP")
if llm_temp_str is not None:
    llm_temp = float(llm_temp_str)

embeddings_type: str = str(os.getenv("EMBEDDINGS_TYPE"))

if embeddings_type == "HF":
    embeddings_model_name = str(os.getenv("HF_EMBEDDINGS"))
elif embeddings_type == "GOOGLE_GENAI" or embeddings_type == "GOOGLE_VERTEXAI":
    embeddings_model_name = str(os.getenv("GOOGLE_EMBEDDINGS"))

embeddings_config = {"type": embeddings_type, "name": embeddings_model_name}

hf_reranker: str = str(os.getenv("HF_RERANKER"))

llm: Union[ChatGoogleGenerativeAI, ChatVertexAI, ChatOllama]

if os.getenv("LLM_MODEL") == "ollama":
    model_name = str(os.getenv("OLLAMA_MODEL"))
    llm = ChatOllama(model=model_name, temperature=llm_temp)

elif os.getenv("LLM_MODEL") == "gemini":
    gemini_model = os.getenv("GOOGLE_GEMINI")
    if gemini_model in {"1_pro", "1.5_flash", "1.5_pro"}:
        raise ValueError(
            f"The selected Gemini model '{gemini_model}' (version 1.0–1.5) is disabled. "
            "Please upgrade to version 2.0 or higher (e.g., 2.0_flash, 2.5_pro)."
        )
    elif gemini_model == "2.0_flash":
        llm = ChatVertexAI(model_name="gemini-2.0-flash", temperature=llm_temp)
    elif gemini_model == "2.5_flash":
        llm = ChatVertexAI(model_name="gemini-2.5-flash", temperature=llm_temp)
    elif gemini_model == "2.5_pro":
        llm = ChatVertexAI(model_name="gemini-2.5-pro", temperature=llm_temp)
    else:
        raise ValueError("GOOGLE_GEMINI environment variable not set to a valid value.")

else:
    raise ValueError("LLM_MODEL environment variable not set to a valid value.")

router = APIRouter(prefix="/chains", tags=["chains"])

hybrid_retriever_chain = HybridRetrieverChain(
    llm_model=llm,
    prompt_template_str=summarise_prompt_template,
    embeddings_config=embeddings_config,
    contextual_rerank=True,
    reranking_model_name=hf_reranker,
    use_cuda=use_cuda,
    markdown_docs_path=["./data/markdown"],
    other_docs_path=["./data/pdf"],
    html_docs_path=["./data/html"],
)
hybrid_retriever_chain.create_hybrid_retriever()
hybrid_retriever = hybrid_retriever_chain.retriever
hybrid_llm_chain = hybrid_retriever_chain.get_llm_chain()

sim_retriever_chain = SimilarityRetrieverChain(
    llm_model=llm,
    prompt_template_str=summarise_prompt_template,
    embeddings_config=embeddings_config,
    use_cuda=use_cuda,
    markdown_docs_path=["./data/markdown"],
    other_docs_path=["./data/pdf"],
    html_docs_path=["./data/html"],
)
sim_retriever_chain.create_similarity_retriever()
sim_llm_chain = sim_retriever_chain.get_llm_chain()


@router.get("/listAll")
async def list_all_chains() -> list[str]:
    return [
        "/graphs/agent-retriever",
        "/chains/hybrid",
        "/chains/sim",
        "/chains/ensemble",
    ]


@router.post("/hybrid", response_model=ChatResponse)
async def get_hybrid_response(user_input: UserInput) -> ChatResponse:
    user_question = user_input.query
    result = hybrid_llm_chain.invoke(user_question)

    context_sources = []
    for i in result["context"]:
        if "url" in i.metadata:
            context_sources.append(
                ContextSource(context=i.page_content, source=i.metadata["url"])
            )
        elif "source" in i.metadata:
            context_sources.append(
                ContextSource(context=i.page_content, source=i.metadata["source"])
            )

    if user_input.list_sources and user_input.list_context:
        response = {"response": result["answer"], "context_sources": context_sources}
    elif user_input.list_sources:
        response = {
            "response": result["answer"],
            "context_sources": [
                ContextSource(context="", source=cs.source) for cs in context_sources
            ],
        }
    elif user_input.list_context:
        response = {
            "response": result["answer"],
            "context_sources": [
                ContextSource(context=cs.context, source="") for cs in context_sources
            ],
        }
    else:
        response = {"response": result["answer"], "context_sources": []}

    return ChatResponse(**response)


@router.post("/hybrid/get_chunks")
async def get_hybrid_chunks(user_input: UserInput) -> dict[str, Any]:
    if hybrid_retriever is not None:
        doc_chunks = hybrid_retriever.invoke(input="placement")
        response = {
            "response": [
                {"page_content": doc.page_content, "src": doc.metadata.get("source")}
                for doc in doc_chunks
            ]
        }
    else:
        raise ValueError("Hybrid retriever not initialized")

    return response


@router.post("/sim")
async def get_sim_response(user_input: UserInput) -> ChatResponse:
    user_question = user_input.query
    result = sim_llm_chain.invoke(user_question)

    context_sources = []
    for i in result["context"]:
        if "url" in i.metadata:
            context_sources.append(
                ContextSource(context=i.page_content, source=i.metadata["url"])
            )
        elif "source" in i.metadata:
            context_sources.append(
                ContextSource(context=i.page_content, source=i.metadata["source"])
            )

    if user_input.list_sources and user_input.list_context:
        response = {"response": result["answer"], "context_sources": context_sources}
    elif user_input.list_sources:
        response = {
            "response": result["answer"],
            "context_sources": [
                ContextSource(context="", source=cs.source) for cs in context_sources
            ],
        }
    elif user_input.list_context:
        response = {
            "response": result["answer"],
            "context_sources": [
                ContextSource(context=cs.context, source="") for cs in context_sources
            ],
        }
    else:
        response = {"response": result["answer"], "context_sources": []}

    return ChatResponse(**response)


@router.post("/sim/get_chunks")
async def get_sim_chunks(user_input: UserInput) -> dict[str, Any]:
    user_question = user_input.query

    if sim_retriever_chain.retriever is not None:
        doc_chunks = sim_retriever_chain.retriever.invoke(input=user_question)
        response = {
            "response": [
                {"page_content": doc.page_content, "src": doc.metadata.get("source")}
                for doc in doc_chunks
            ]
        }
    else:
        raise ValueError("Similarity retriever not initialized")

    return response
