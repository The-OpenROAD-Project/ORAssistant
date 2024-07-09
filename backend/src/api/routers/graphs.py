import os

from fastapi import APIRouter
from pydantic import BaseModel

from ...agents.retriever_graph import RetrieverGraph

from langchain_google_vertexai import ChatVertexAI
from langchain_google_genai import ChatGoogleGenerativeAI

from dotenv import load_dotenv


class UserInput(BaseModel):
    query: str
    list_sources: bool = False
    list_context: bool = False


load_dotenv()

use_cuda = os.getenv("USE_CUDA")

if os.getenv("GOOGLE_GEMINI") == "1_pro":
    llm = ChatGoogleGenerativeAI(model="gemini-pro", temperature=1)
elif os.getenv("GOOGLE_GEMINI") == "1.5_flash":
    llm = ChatVertexAI(model_name="gemini-1.5-flash")
elif os.getenv("GOOGLE_GEMINI") == "1.5_pro":
    llm = ChatVertexAI(model_name="gemini-1.5-pro")

hf_embdeddings = os.getenv("HF_EMBEDDINGS")
hf_reranker = os.getenv("HF_RERANKER")


router = APIRouter(prefix="/graphs", tags=["graphs"])

rg = RetrieverGraph(llm_model=llm)
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
