from fastapi import APIRouter, Request, Response
from fastapi.responses import StreamingResponse
import httpx
import os

router = APIRouter(prefix="/ui", tags=["ui"])

BACKEND_ENDPOINT = os.getenv("BACKEND_ENDPOINT", "http://localhost:8000")
# Keep a streaming-capable client as well (no timeout for long SSE responses)
client = httpx.AsyncClient(base_url=BACKEND_ENDPOINT)
stream_client = httpx.AsyncClient(base_url=BACKEND_ENDPOINT, timeout=None)


@router.post("/chat")
async def proxy_chat(request: Request) -> Response | StreamingResponse:
    """Proxy to the backend chat endpoint.

    Reads the ``stream`` field from the JSON body.  When ``stream=true`` the
    response is forwarded as a Server-Sent Events stream so tokens reach the
    browser in real time.  When ``stream=false`` (default) the full JSON
    payload is returned once generation completes.
    """
    data = await request.json()
    wants_stream: bool = bool(data.get("stream", False))

    if wants_stream:
        # Open a persistent streaming connection and forward chunks as-is.
        async def _iter_sse():
            async with stream_client.stream(
                "POST", "/conversations/agent-retriever", json=data
            ) as resp:
                async for chunk in resp.aiter_text():
                    yield chunk

        return StreamingResponse(_iter_sse(), media_type="text/event-stream")

    # Non-streaming: wait for the full response, then return it.
    resp = await client.post("/conversations/agent-retriever", json=data)
    return Response(
        content=resp.content,
        status_code=resp.status_code,
        media_type=resp.headers.get("content-type"),
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
