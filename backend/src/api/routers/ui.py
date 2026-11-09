from fastapi import APIRouter, Request, Response
from fastapi.responses import StreamingResponse
from starlette.types import Receive, Scope, Send
import anyio
import httpx
import os

router = APIRouter(prefix="/ui", tags=["ui"])

BACKEND_ENDPOINT = os.getenv("BACKEND_ENDPOINT", "http://localhost:8000")
# The read timeout limits the wait for each chunk. A JSON answer arrives
# only after the whole generation, and the first streamed token waits for
# retrieval, so 5 s would cut both. The other limits stay at 5 s, so a
# down backend still fails fast.
client = httpx.AsyncClient(
    base_url=BACKEND_ENDPOINT, timeout=httpx.Timeout(5.0, read=300.0)
)


class _BackendStreamResponse(StreamingResponse):
    """Forwards a streamed backend response and always closes it.

    Starlette skips a background task when the body raises, and on ASGI
    spec 2.4 it leaves the body iterator open after a client disconnect.
    Closing here frees the shared client's connection on every path.
    """

    def __init__(self, backend_response: httpx.Response) -> None:
        super().__init__(
            backend_response.aiter_bytes(),
            status_code=backend_response.status_code,
            media_type=backend_response.headers.get("content-type"),
        )
        self.backend_response = backend_response

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        try:
            await super().__call__(scope, receive, send)
        finally:
            # Shield the close, so a cancelled request still releases it.
            with anyio.CancelScope(shield=True):
                await self.backend_response.aclose()


@router.post("/chat")
async def proxy_chat(request: Request) -> StreamingResponse:
    data = await request.json()
    # TODO: set this route dynamically
    backend_request = client.build_request(
        "POST", "/conversations/agent-retriever", json=data
    )
    # Forward each chunk as it arrives, so "stream": true in the body
    # reaches the caller as a live event stream.
    return _BackendStreamResponse(await client.send(backend_request, stream=True))


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
