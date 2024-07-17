import os
from typing import Any

from fastapi import APIRouter
from pydantic import BaseModel

from ...chains.hybrid_retriever_chain import HybridRetrieverChain
from ...chains.similarity_retriever_chain import SimilarityRetrieverChain
from ...chains.multi_retriever_chain import MultiRetrieverChain

from ...prompts.answer_prompts import summarise_prompt_template

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
    llm = ChatGoogleGenerativeAI(model='gemini-pro', temperature=llm_temp)  # type: ignore
elif os.getenv('GOOGLE_GEMINI') == '1.5_flash':
    llm = ChatVertexAI(model_name='gemini-1.5-flash', temperature=llm_temp)
elif os.getenv('GOOGLE_GEMINI') == '1.5_pro':
    llm = ChatVertexAI(model_name='gemini-1.5-pro', temperature=llm_temp)
else:
    raise ValueError('GOOGLE_GEMINI environment variable not set to a valid value.')

router = APIRouter(prefix='/chains', tags=['chains'])

hybrid_retriever = HybridRetrieverChain(
    llm_model=llm,
    prompt_template_str=summarise_prompt_template,
    embeddings_model_name=hf_embdeddings,
    reranking_model_name=hf_reranker,
    contextual_rerank=True,
    use_cuda=use_cuda,
    docs_path=['./data/markdown/ORFS_docs', './data/markdown/OR_docs'],
    manpages_path=['./data/markdown/manpages'],
    pdfs_path=['./data/pdf/OpenSTA/OpenSTA_docs.pdf'],
)
hybrid_retriever.create_hybrid_retriever()
hybrid_llm_chain = hybrid_retriever.get_llm_chain()

sim_retriever_chain = SimilarityRetrieverChain(
    llm_model=llm,
    prompt_template_str=summarise_prompt_template,
    embeddings_model_name=hf_embdeddings,
    use_cuda=use_cuda,
    docs_path=['./data/markdown/ORFS_docs', './data/markdown/OR_docs'],
    manpages_path=['./data/markdown/manpages'],
    pdfs_path=['./data/pdf/OpenSTA/OpenSTA_docs.pdf'],
)
sim_retriever_chain.create_similarity_retriever()
sim_llm_chain = sim_retriever_chain.get_llm_chain()

multi_retriever_chain = MultiRetrieverChain(
    llm_model=llm,
    prompt_template_str=summarise_prompt_template,
    embeddings_model_name=hf_embdeddings,
    use_cuda=use_cuda,
    docs_path=['./data/markdown/ORFS_docs', './data/markdown/OR_docs'],
    manpages_path=['./data/markdown/manpages'],
)
multi_retriever_chain.create_multi_retriever()
multi_llm_chain = multi_retriever_chain.get_llm_chain()


@router.get('/listAll')
async def list_all_chains() -> list[str]:
    return [
        '/graphs/agent-retriever',
        '/chains/hybrid',
        '/chains/sim',
        '/chains/ensemble',
    ]


@router.post('/hybrid')
async def get_hybrid_response(user_input: UserInput) -> dict[str, Any]:
    user_question = user_input.query
    result = hybrid_llm_chain.invoke(user_question)

    links = []
    context = []
    for i in result['context']:
        if 'url' in i.metadata:
            links.append(i.metadata['url'])
        elif 'source' in i.metadata:
            links.append(i.metadata['source'])
        context.append(i.page_content)

    links = list(set(links))
    links = list(set(links))

    if user_input.list_sources and user_input.list_context:
        response = {
            'response': result['answer'],
            'sources': (links),
            'context': (context),
        }
    elif user_input.list_sources:
        response = {'response': result['answer'], 'sources': (links)}
    elif user_input.list_context:
        response = {'response': result['answer'], 'context': (context)}
    else:
        response = {'response': result['answer']}

    return response


@router.post('/sim')
async def get_sim_response(user_input: UserInput) -> dict[str, Any]:
    user_question = user_input.query
    result = hybrid_llm_chain.invoke(user_question)

    links = []
    context = []
    for i in result['context']:
        if 'url' in i.metadata:
            links.append(i.metadata['url'])
        elif 'source' in i.metadata:
            links.append(i.metadata['source'])
        context.append(i.page_content)

    links = list(set(links))

    if user_input.list_sources and user_input.list_context:
        response = {
            'response': result['answer'],
            'sources': (links),
            'context': (context),
        }
    elif user_input.list_sources:
        response = {'response': result['answer'], 'sources': (links)}
    elif user_input.list_context:
        response = {'response': result['answer'], 'context': (context)}
    else:
        response = {'response': result['answer']}

    return response


@router.post('/ensemble')
async def get_response(user_input: UserInput) -> dict[str, Any]:
    user_question = user_input.query
    result = hybrid_llm_chain.invoke(user_question)

    links = []
    context = []
    for i in result['context']:
        if 'url' in i.metadata:
            links.append(i.metadata['url'])
        elif 'source' in i.metadata:
            links.append(i.metadata['source'])
        context.append(i.page_content)

    links = list(set(links))
    links = list(set(links))

    if user_input.list_sources and user_input.list_context:
        response = {
            'response': result['answer'],
            'sources': (links),
            'context': (context),
        }
    elif user_input.list_sources:
        response = {'response': result['answer'], 'sources': (links)}
    elif user_input.list_context:
        response = {'response': result['answer'], 'context': (context)}
    else:
        response = {'response': result['answer']}

    return response
