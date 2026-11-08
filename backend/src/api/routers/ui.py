from fastapi import APIRouter, Request, Response
from fastapi.responses import StreamingResponse
from starlette.background import BackgroundTask
import httpx
import os

router = APIRouter(prefix="/ui", tags=["ui"])

BACKEND_ENDPOINT = os.getenv("BACKEND_ENDPOINT", "http://localhost:8000")
client = httpx.AsyncClient(base_url=BACKEND_ENDPOINT)


@router.post("/chat")
async def proxy_chat(request: Request) -> StreamingResponse:
    data = await request.json()
    # TODO: set this route dynamically
    backend_request = client.build_request(
        "POST", "/conversations/agent-retriever", json=data
    )
    # Forward each chunk as it arrives, so "stream": true in the body
    # reaches the caller as a live event stream.
    resp = await client.send(backend_request, stream=True)
    return StreamingResponse(
        resp.aiter_bytes(),
        status_code=resp.status_code,
        media_type=resp.headers.get("content-type"),
        background=BackgroundTask(resp.aclose),
    )


@router.post("/suggestedQuestions")
async def suggested_questions(request: Request) -> Response:
    data = await request.json()
    # Transform camelCase to snake_case for the backend
    transformed_data = {
        "latest_question": data.get("latestQuestion", ""),
        "assistant_answer": data.get("assistantAnswer", ""),
    }
    resp = await client.post("/helpers/suggestedQuestions", json=transformed_data)
    return Response(
        content=resp.content,
        status_code=resp.status_code,
        media_type=resp.headers.get("content-type"),
    )
