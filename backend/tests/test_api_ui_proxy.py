"""HTTP tests for the POST /ui/chat proxy to the chat endpoint."""

import asyncio
import json
from unittest.mock import patch

import httpx
from fastapi import FastAPI

from src.api.routers import ui


async def call_proxy(body: dict, on_body_chunk=lambda: None) -> tuple[dict, bytes]:
    """Send POST /ui/chat over ASGI; return the response start and body."""
    app = FastAPI()
    app.include_router(ui.router)
    scope = {
        "type": "http",
        "asgi": {"version": "3.0", "spec_version": "2.4"},
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

    async def receive() -> dict:
        return {
            "type": "http.request",
            "body": json.dumps(body).encode(),
            "more_body": False,
        }

    start: dict = {}
    chunks: list[bytes] = []

    async def send(message: dict) -> None:
        if message["type"] == "http.response.start":
            start.update(message)
        elif message["type"] == "http.response.body" and message.get("body"):
            chunks.append(message["body"])
            on_body_chunk()

    await asyncio.wait_for(app(scope, receive, send), timeout=5)
    return start, b"".join(chunks)


def content_type(start: dict) -> str:
    return dict(start["headers"])[b"content-type"].decode()


async def test_stream_true_forwards_each_chunk_as_it_arrives():
    # The backend holds back its last chunk until the client has the first.
    first_chunk_delivered = asyncio.Event()
    forwarded: list[dict] = []

    async def backend_body():
        yield b"OpenROAD \n\n"
        await first_chunk_delivered.wait()
        yield b"Sources: \n\n"

    def backend(request: httpx.Request) -> httpx.Response:
        forwarded.append(json.loads(request.content))
        return httpx.Response(
            200,
            headers={"content-type": "text/event-stream; charset=utf-8"},
            content=backend_body(),
        )

    body = {"query": "What is OpenROAD?", "stream": True}
    backend_client = httpx.AsyncClient(
        transport=httpx.MockTransport(backend), base_url="http://backend"
    )
    with patch.object(ui, "client", backend_client):
        start, received = await call_proxy(body, first_chunk_delivered.set)

    assert forwarded == [body]
    assert start["status"] == 200
    assert content_type(start).startswith("text/event-stream")
    assert received == b"OpenROAD \n\nSources: \n\n"


async def test_stream_absent_forwards_the_json_answer():
    answer = {"response": "OpenROAD is a tool.", "context_sources": [], "tools": []}

    def backend(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json=answer)

    backend_client = httpx.AsyncClient(
        transport=httpx.MockTransport(backend), base_url="http://backend"
    )
    with patch.object(ui, "client", backend_client):
        start, received = await call_proxy({"query": "What is OpenROAD?"})

    assert start["status"] == 200
    assert content_type(start) == "application/json"
    assert json.loads(received) == answer
