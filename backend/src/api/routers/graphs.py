import os

from fastapi import APIRouter
from pydantic import BaseModel

from ...agents.retriever_graph import RetrieverGraph

from langchain_google_vertexai import ChatVertexAI
from langchain_google_genai import ChatGoogleGenerativeAI

from dotenv import load_dotenv

from typing import Union


class UserInput(BaseModel):
    query: str
    list_sources: bool = False
    list_context: bool = False


load_dotenv()

required_env_vars = [
    "USE_CUDA",
    "GEMINI_TEMP",
    "HF_EMBEDDINGS",
    "HF_RERANKER",
    "GOOGLE_GEMINI",
]

if any(os.getenv(var) is None for var in required_env_vars):
    raise ValueError("One or more environment variables are not set.")

if os.getenv("USE_CUDA").lower() in ('true'):
    use_cuda:bool = True
else:
    use_cuda:bool = False
llm_temp: float = os.getenv("GEMINI_TEMP")
hf_embdeddings: str = os.getenv("HF_EMBEDDINGS")
hf_reranker: str = os.getenv("HF_RERANKER")

llm: Union[ChatGoogleGenerativeAI, ChatVertexAI]

if os.getenv("GOOGLE_GEMINI") == "1_pro":
    llm = ChatGoogleGenerativeAI(model="gemini-pro", temperature=llm_temp)
elif os.getenv("GOOGLE_GEMINI") == "1.5_flash":
    llm = ChatVertexAI(model_name="gemini-1.5-flash", temperature=llm_temp)
elif os.getenv("GOOGLE_GEMINI") == "1.5_pro":
    llm = ChatVertexAI(model_name="gemini-1.5-pro", temperature=llm_temp)
else:
    raise ValueError("GOOGLE_GEMINI environment variable not set to a valid value.")

router = APIRouter(prefix="/graphs", tags=["graphs"])

rg = RetrieverGraph(
    llm_model=llm,
    embeddings_model_name=hf_embdeddings,
    reranking_model_name=hf_reranker,
    use_cuda=use_cuda,
)
rg.initialize()


@router.post("/agent-retriever")
async def get_agent_response(user_input: UserInput) -> dict:
    user_question = user_input.query
    inputs = {
        "messages": [
            ("user", user_question),
        ]
    }

    output = list(rg.graph.stream(inputs))

    tool = output[0]["agent"]["tools"][0]["name"]

    context = output[1][tool]["context"]
    sources = output[1][tool]["sources"]
    response = output[2]["generate"]["messages"][0]

    if user_input.list_sources and user_input.list_context:
        response = {
            "response": response,
            "sources": (sources),
            "context": (context),
        }
    elif user_input.list_sources:
        response = {"response": response, "sources": (sources)}
    elif user_input.list_context:
        response = {"response": response, "context": (context)}
    else:
        response = {"response": response}

    return response
