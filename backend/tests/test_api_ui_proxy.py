"""HTTP tests for the POST /ui/chat proxy to the chat endpoint."""

import asyncio
import json
from collections.abc import AsyncIterator, Callable
from unittest.mock import patch

import httpx
import pytest
from fastapi import FastAPI
from starlette.requests import ClientDisconnect

from src.api.routers import ui


class BackendStream(httpx.AsyncByteStream):
    """Backend response body that records when the proxy closes it."""

    def __init__(self, body: AsyncIterator[bytes]) -> None:
        self.body = body
        self.closed = False

    async def __aiter__(self) -> AsyncIterator[bytes]:
        async for chunk in self.body:
            yield chunk

    async def aclose(self) -> None:
        # A real close awaits socket I/O, so a cancelled caller can miss it.
        await asyncio.sleep(0)
        self.closed = True


def backend_client(handler: Callable[[httpx.Request], httpx.Response]):
    return httpx.AsyncClient(
        transport=httpx.MockTransport(handler), base_url="http://backend"
    )


async def call_proxy(
    body: dict,
    spec_version: str,
    on_body_chunk: Callable[[], None] = lambda: None,
    disconnect_after_first_chunk: bool = False,
) -> tuple[dict, bytes]:
    """Send POST /ui/chat over ASGI; return the response start and body.

    Uvicorn reports ASGI spec 2.3, where Starlette listens for a disconnect
    while it streams. With 2.4, a disconnect shows as an OSError from send.
    """
    app = FastAPI()
    app.include_router(ui.router)
    scope = {
        "type": "http",
        "asgi": {"version": "3.0", "spec_version": spec_version},
        "http_version": "1.1",
        "method": "POST",
        "scheme": "http",
        "path": "/ui/chat",
        "raw_path": b"/ui/chat",
        "root_path": "",
        "query_string": b"",
        "headers": [(b"content-type", b"application/json")],
        "client": ("testclient", 50000),
        "server": ("testserver", 80),
    }

    request_sent = False
    disconnected = asyncio.Event()

    async def receive() -> dict:
        nonlocal request_sent
        if not request_sent:
            request_sent = True
            return {
                "type": "http.request",
                "body": json.dumps(body).encode(),
                "more_body": False,
            }
        await disconnected.wait()
        return {"type": "http.disconnect"}

    start: dict = {}
    chunks: list[bytes] = []

    async def send(message: dict) -> None:
        if message["type"] == "http.response.start":
            start.update(message)
        elif message["type"] == "http.response.body":
            if not message.get("more_body", False):
                disconnected.set()
            if message.get("body"):
                if disconnect_after_first_chunk:
                    disconnected.set()
                    if spec_version >= "2.4":
                        raise OSError("client went away")
                chunks.append(message["body"])
                on_body_chunk()

    await asyncio.wait_for(app(scope, receive, send), timeout=5)
    return start, b"".join(chunks)


def content_type(start: dict) -> str:
    return dict(start["headers"])[b"content-type"].decode()


@pytest.fixture(params=["2.3", "2.4"])
def spec_version(request) -> str:
    return request.param


async def test_stream_true_forwards_each_chunk_as_it_arrives(spec_version):
    # The backend holds back its last chunk until the client has the first.
    first_chunk_delivered = asyncio.Event()
    forwarded: list[dict] = []

    async def backend_body():
        yield b"OpenROAD \n\n"
        await first_chunk_delivered.wait()
        yield b"Sources: \n\n"

    stream = BackendStream(backend_body())

    def backend(request: httpx.Request) -> httpx.Response:
        forwarded.append(json.loads(request.content))
        return httpx.Response(
            200,
            headers={"content-type": "text/event-stream; charset=utf-8"},
            stream=stream,
        )

    body = {"query": "What is OpenROAD?", "stream": True}
    with patch.object(ui, "client", backend_client(backend)):
        start, received = await call_proxy(
            body, spec_version, first_chunk_delivered.set
        )

    assert forwarded == [body]
    assert start["status"] == 200
    assert content_type(start).startswith("text/event-stream")
    assert received == b"OpenROAD \n\nSources: \n\n"
    assert stream.closed


async def test_stream_absent_forwards_the_json_answer(spec_version):
    answer = {"response": "OpenROAD is a tool.", "context_sources": [], "tools": []}

    def backend(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json=answer)

    with patch.object(ui, "client", backend_client(backend)):
        start, received = await call_proxy({"query": "What is OpenROAD?"}, spec_version)

    assert start["status"] == 200
    assert content_type(start) == "application/json"
    assert json.loads(received) == answer


async def test_backend_read_error_closes_the_backend_response(spec_version):
    async def backend_body():
        yield b"OpenROAD \n\n"
        raise httpx.ReadError("backend went away")

    stream = BackendStream(backend_body())

    def backend(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, stream=stream)

    with patch.object(ui, "client", backend_client(backend)):
        with pytest.raises(httpx.ReadError):
            await call_proxy({"query": "q", "stream": True}, spec_version)

    assert stream.closed


async def test_client_disconnect_closes_the_backend_response(spec_version):
    async def backend_body():
        yield b"OpenROAD \n\n"
        await asyncio.Event().wait()  # The answer is still being generated.
        yield b"never sent"

    stream = BackendStream(backend_body())

    def backend(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, stream=stream)

    with patch.object(ui, "client", backend_client(backend)):
        try:
            await call_proxy(
                {"query": "q", "stream": True},
                spec_version,
                disconnect_after_first_chunk=True,
            )
        except ClientDisconnect:
            pass  # Starlette raises this for a disconnect on ASGI spec 2.4.

    assert stream.closed
