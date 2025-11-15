import os
import logging
from dotenv import load_dotenv

from typing import Any
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException
from langchain_google_vertexai import ChatVertexAI
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_ollama import ChatOllama
from langchain_core.messages import AIMessageChunk
from starlette.responses import StreamingResponse
from sqlalchemy.orm import Session

from ...agents.retriever_graph import RetrieverGraph
from ...database import get_db
from ...database import crud
from ..models.response_model import (
    ChatResponse,
    ContextSource,
    UserInput,
    ConversationResponse,
    ConversationListResponse,
)

load_dotenv()
logging.basicConfig(level=os.environ.get("LOGLEVEL", "INFO").upper())

required_env_vars = [
    "USE_CUDA",
    "LLM_TEMP",
    "HF_EMBEDDINGS",
    "HF_RERANKER",
    "LLM_MODEL",
]

missing_vars = [var for var in required_env_vars if os.getenv(var) is None]
if missing_vars:
    raise ValueError(
        f"The following environment variables are not set: {', '.join(missing_vars)}"
    )

use_cuda: bool = False
llm_temp: float = 0.0
fast_mode: bool = False
debug: bool = False
enable_mcp: bool = False

if str(os.getenv("USE_CUDA")).lower() in ("true"):
    use_cuda = True

if str(os.getenv("FAST_MODE")).lower() in ("true"):
    fast_mode = True

if str(os.getenv("DEBUG")).lower() in ("true"):
    debug = True

if str(os.getenv("ENABLE_MCP")).lower() in ("true"):
    enable_mcp = True

llm_temp_str = os.getenv("LLM_TEMP")
if llm_temp_str is not None:
    llm_temp = float(llm_temp_str)

embeddings_type: str = str(os.getenv("EMBEDDINGS_TYPE"))

if embeddings_type == "HF":
    embeddings_model_name = str(os.getenv("HF_EMBEDDINGS"))
elif embeddings_type == "GOOGLE_GENAI" or embeddings_type == "GOOGLE_VERTEXAI":
    embeddings_model_name = str(os.getenv("GOOGLE_EMBEDDINGS"))
else:
    raise ValueError(
        "EMBEDDINGS_TYPE environment variable must be set to 'HF', 'GOOGLE_GENAI', or 'GOOGLE_VERTEXAI'."
    )

embeddings_config = {"type": embeddings_type, "name": embeddings_model_name}

hf_reranker: str = str(os.getenv("HF_RERANKER"))

llm: ChatGoogleGenerativeAI | ChatVertexAI | ChatOllama

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
        llm = ChatGoogleGenerativeAI(model="gemini-2.0-flash", temperature=llm_temp)
    elif gemini_model == "2.5_flash":
        llm = ChatVertexAI(model_name="gemini-2.5-flash", temperature=llm_temp)
    elif gemini_model == "2.5_pro":
        llm = ChatVertexAI(model_name="gemini-2.5-pro", temperature=llm_temp)
    else:
        raise ValueError("GOOGLE_GEMINI environment variable not set to a valid value.")

else:
    raise ValueError("LLM_MODEL environment variable not set to a valid value.")

router = APIRouter(prefix="/conversations", tags=["conversations"])


def extract_rag_context_sources(output: list) -> list[ContextSource]:
    context_sources = []
    for element in output[1:-1]:
        if isinstance(element, dict):
            for key, value in element.items():
                if key.startswith("retrieve_") and isinstance(value, dict):
                    urls = value.get("urls", [])
                    context = value.get("context", "")
                    for url in urls:
                        context_sources.append(
                            ContextSource(context=context, source=url)
                        )
    return context_sources


def extract_mcp_context_sources(output: list) -> tuple[list[ContextSource], list[str]]:
    context_sources = []
    tools = []

    if "agent" in output[0] and "tools" in output[0]["agent"]:
        tools = output[0]["agent"]["tools"]
        for tool_index in range(len(tools)):
            tool_output = list(output[tool_index + 1].values())[0]
            urls = tool_output.get("urls", [])
            context_list = tool_output.get("context_list", [])
            for _url, _context in zip(urls, context_list):
                context_sources.append(ContextSource(context=_context, source=_url))

    return context_sources, tools


def validate_output_structure(output: Any) -> bool:
    return isinstance(output, list) and len(output) > 2 and isinstance(output[-1], dict)


def log_invalid_output(output: Any) -> None:
    logging.error(
        f"Invalid output structure: type={type(output)}, len={len(output) if isinstance(output, list) else 'N/A'}"
    )
    if isinstance(output, list) and len(output) > 0:
        logging.error(
            f"Last element keys: {output[-1].keys() if isinstance(output[-1], dict) else 'Not a dict'}"
        )


def get_agent_type(output: list) -> tuple[bool, str]:
    is_rag_agent = "rag_generate" in output[-1]
    generate_key = "rag_generate" if is_rag_agent else "generate"
    return is_rag_agent, generate_key


def extract_llm_response(output: list, generate_key: str) -> str | None:
    if generate_key not in output[-1]:
        logging.error(f"Missing {generate_key} key")
        return None

    generate_data = output[-1][generate_key]

    if "messages" not in generate_data:
        logging.error(f"Missing messages in {generate_key}")
        return None

    messages = generate_data["messages"]
    if not messages or len(messages) == 0:
        logging.error("No messages in generate output")
        return None

    return str(messages[0])


def parse_agent_output(output: list) -> tuple[str, list[ContextSource], list[str]]:
    default_response = "LLM response extraction failed"
    context_sources: list[ContextSource] = []
    tools: list[str] = []

    if not validate_output_structure(output):
        log_invalid_output(output)
        return default_response, context_sources, tools

    is_rag_agent, generate_key = get_agent_type(output)

    llm_response = extract_llm_response(output, generate_key)
    if llm_response is None:
        return default_response, context_sources, tools

    if is_rag_agent:
        context_sources = extract_rag_context_sources(output)
    else:
        context_sources, tools = extract_mcp_context_sources(output)

    return llm_response, context_sources, tools


rg = RetrieverGraph(
    llm_model=llm,
    embeddings_config=embeddings_config,
    reranking_model_name=hf_reranker,
    use_cuda=use_cuda,
    inbuilt_tool_calling=True,
    fast_mode=fast_mode,
    debug=debug,
    enable_mcp=enable_mcp,
)
rg.initialize()


def get_history_str(db: Session, conversation_uuid: UUID) -> str:
    history = crud.get_conversation_history(db, conversation_uuid)
    history_str = ""
    for i in history:
        user_msg = i.get("User", "")
        ai_msg = i.get("AI", "")
        if user_msg and ai_msg:
            history_str += f"User : {user_msg}\nAI : {ai_msg}\n\n"
    return history_str


@router.post("/agent-retriever", response_model=ChatResponse)
async def get_agent_response(
    user_input: UserInput, db: Session = Depends(get_db)
) -> ChatResponse:
    """Processes a user query using the retriever agent, maintains conversation context, and returns the generated response along with relevant context sources and tools used."""
    user_question = user_input.query

    conversation_uuid = user_input.conversation_uuid

    conversation = crud.get_or_create_conversation(
        db,
        conversation_uuid=conversation_uuid,
        title=user_question[:100] if user_question else None,
    )

    crud.create_message(
        db=db,
        conversation_uuid=conversation.uuid,
        role="user",
        content=user_question,
    )

    inputs = {
        "messages": [
            ("user", user_question),
        ],
        "chat_history": get_history_str(db, conversation.uuid),
    }

    if rg.graph is not None:
        output = list(rg.graph.stream(inputs, stream_mode="updates"))
    else:
        raise ValueError("RetrieverGraph not initialized.")

    llm_response, context_sources, tools = parse_agent_output(output)

    context_sources_dict: dict[str, Any] = {
        "sources": [
            {"source": cs.source, "context": cs.context} for cs in context_sources
        ]
    }
    crud.create_message(
        db=db,
        conversation_uuid=conversation.uuid,
        role="assistant",
        content=llm_response,
        context_sources=context_sources_dict,
        tools=tools,
    )

    response: dict[str, Any]
    if user_input.list_sources and user_input.list_context:
        response = {
            "response": llm_response,
            "context_sources": context_sources,
            "tools": tools,
        }
    elif user_input.list_sources:
        response = {
            "response": llm_response,
            "context_sources": [
                ContextSource(context="", source=cs.source) for cs in context_sources
            ],
            "tools": tools,
        }
    elif user_input.list_context:
        response = {
            "response": llm_response,
            "context_sources": [
                ContextSource(context=cs.context, source="") for cs in context_sources
            ],
            "tools": tools,
        }
    else:
        response = {
            "response": llm_response,
            "context_sources": [ContextSource(context="", source="")],
            "tools": tools,
        }

    return ChatResponse(**response)


async def get_response_stream(user_input: UserInput, db: Session) -> Any:
    user_question = user_input.query

    conversation_uuid = user_input.conversation_uuid

    conversation = crud.get_or_create_conversation(
        db,
        conversation_uuid=conversation_uuid,
        title=user_question[:100] if user_question else None,
    )

    crud.create_message(
        db=db,
        conversation_uuid=conversation.uuid,
        role="user",
        content=user_question,
    )

    inputs = {
        "messages": [
            ("user", user_question),
        ],
        "chat_history": get_history_str(db, conversation.uuid),
    }

    urls: list[str] = []
    current_llm_call_count = 1
    chunks: list[str] = []

    if rg.graph is not None:
        async for event in rg.graph.astream_events(inputs, version="v2"):
            chunk = event["event"]

            if chunk == "on_chat_model_end":
                current_llm_call_count += 1

            if chunk == "on_retriever_start" or chunk == "on_retriever_end":
                event_data: Any = event.get("data", {})
                output_docs: list[Any] = event_data.get("output", [])
                for document in output_docs:
                    urls.append(document.metadata["url"])

            if chunk == "on_chat_model_stream" and current_llm_call_count >= 2:
                event_data_chunk: Any = event.get("data", {})
                message_content: Any = event_data_chunk.get("chunk", {})
                if isinstance(message_content, AIMessageChunk):
                    msg = message_content.content
                else:
                    msg = None

                if msg:
                    chunks.append(str(msg))
                    yield str(msg) + "\n\n"

    urls = list(set(urls))
    yield f"Sources: {', '.join(urls)}\n\n"

    full_response = "".join(chunks)
    context_sources_dict: dict[str, Any] = {
        "sources": [{"source": url, "context": ""} for url in urls]
    }
    crud.create_message(
        db=db,
        conversation_uuid=conversation.uuid,
        role="assistant",
        content=full_response,
        context_sources=context_sources_dict,
        tools=[],
    )


@router.post("/agent-retriever/stream", response_class=StreamingResponse)
async def get_agent_response_streaming(
    user_input: UserInput, db: Session = Depends(get_db)
) -> StreamingResponse:
    """Provides real-time streaming of the agent's response as it's being generated."""
    return StreamingResponse(
        get_response_stream(user_input, db), media_type="text/event-stream"
    )


@router.post("", response_model=ConversationResponse, status_code=201)
async def create_conversation(db: Session = Depends(get_db)) -> ConversationResponse:
    """Creates a new conversation with an auto-generated UUID identifier."""
    new_conversation = crud.create_conversation(db, conversation_uuid=None, title=None)
    return ConversationResponse.model_validate(new_conversation)


@router.get("", response_model=list[ConversationListResponse])
async def list_conversations(
    skip: int = 0, limit: int = 100, db: Session = Depends(get_db)
) -> list[ConversationListResponse]:
    """Retrieves a paginated list of all conversations without their messages."""
    conversations = crud.get_all_conversations(db, skip=skip, limit=limit)
    return [ConversationListResponse.model_validate(conv) for conv in conversations]


@router.get("/{id}", response_model=ConversationResponse)
async def get_conversation(
    id: UUID, db: Session = Depends(get_db)
) -> ConversationResponse:
    """Retrieves a complete conversation including all associated messages."""
    conversation = crud.get_conversation(db, id)
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")
    return ConversationResponse.model_validate(conversation)


@router.delete("/{id}", status_code=204)
async def delete_conversation(id: UUID, db: Session = Depends(get_db)) -> None:
    """Permanently removes a conversation and all associated messages from the database."""
    conversation = crud.get_conversation(db, id)
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")
    crud.delete_conversation(db, id)
