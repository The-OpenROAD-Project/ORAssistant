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
    'USE_CUDA',
    'GEMINI_TEMP',
    'HF_EMBEDDINGS',
    'HF_RERANKER',
    'GOOGLE_GEMINI',
]

if any(os.getenv(var) is None for var in required_env_vars):
    raise ValueError('One or more environment variables are not set.')

use_cuda: bool = False
llm_temp: float = 0.0

if str(os.getenv('USE_CUDA')).lower() in ('true'):
    use_cuda = True

llm_temp_str = os.getenv('GEMINI_TEMP')
if llm_temp_str is not None:
    llm_temp = float(llm_temp_str)

hf_embdeddings: str = str(os.getenv('HF_EMBEDDINGS'))
hf_reranker: str = str(os.getenv('HF_RERANKER'))

llm: Union[ChatGoogleGenerativeAI, ChatVertexAI]

if os.getenv('GOOGLE_GEMINI') == '1_pro':
    llm = ChatGoogleGenerativeAI(model='gemini-pro', temperature=llm_temp)
elif os.getenv('GOOGLE_GEMINI') == '1.5_flash':
    llm = ChatVertexAI(model_name='gemini-1.5-flash', temperature=llm_temp)
elif os.getenv('GOOGLE_GEMINI') == '1.5_pro':
    llm = ChatVertexAI(model_name='gemini-1.5-pro', temperature=llm_temp)
else:
    raise ValueError('GOOGLE_GEMINI environment variable not set to a valid value.')

router = APIRouter(prefix='/graphs', tags=['graphs'])

rg = RetrieverGraph(
    llm_model=llm,
    embeddings_model_name=hf_embdeddings,
    reranking_model_name=hf_reranker,
    use_cuda=use_cuda,
)
rg.initialize()


@router.post('/agent-retriever')
async def get_agent_response(user_input: UserInput) -> dict[str, Union[str, list[str]]]:
    user_question = user_input.query
    inputs = {
        'messages': [
            ('user', user_question),
        ]
    }

    if rg.graph is not None:
        output = list(rg.graph.stream(inputs))
    else:
        raise ValueError('RetrieverGraph not initialized.')

    tool = list(output)[0]['agent']['tools'][0]['name']
    context = output[1][tool]['context']
    sources = output[1][tool]['sources']
    llm_response = output[2]['generate']['messages'][0]

    if user_input.list_sources and user_input.list_context:
        response = {
            'response': llm_response,
            'sources': (sources),
            'context': (context),
        }
    elif user_input.list_sources:
        response = {'response': llm_response, 'sources': (sources)}
    elif user_input.list_context:
        response = {'response': llm_response, 'context': (context)}
    else:
        response = {'response': llm_response}

    return response
