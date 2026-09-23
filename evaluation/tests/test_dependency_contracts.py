"""Regression tests for external APIs used by the evaluation package."""

import asyncio
import json
import socketserver
import threading
import unittest
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

import requests
from deepeval import evaluate
from google.genai import errors

from auto_evaluation.eval_main import EvaluationHarness
from auto_evaluation.src.models.gemini import GoogleGeminiLangChain


class QueryHandler(socketserver.StreamRequestHandler):
    """Record the request path and return a valid retriever response."""

    path_seen = ""

    def handle(self) -> None:
        request_line = self.rfile.readline().decode().strip()
        QueryHandler.path_seen = request_line.split()[1]
        while self.rfile.readline() not in (b"\r\n", b"\n", b""):
            pass

        body = json.dumps(
            {"response": "ok", "context_sources": [], "tools": []}
        ).encode()
        self.wfile.write(
            b"HTTP/1.1 200 OK\r\n"
            b"Content-Type: application/json\r\n"
            + f"Content-Length: {len(body)}\r\n".encode()
            + b"Connection: close\r\n\r\n"
            + body
        )


class UnavailableQueryHandler(socketserver.StreamRequestHandler):
    """Return the backend status used while the graph is unavailable."""

    def handle(self) -> None:
        self.rfile.readline()
        while self.rfile.readline() not in (b"\r\n", b"\n", b""):
            pass
        self.wfile.write(
            b"HTTP/1.1 503 Service Unavailable\r\n"
            b"Content-Length: 0\r\n"
            b"Connection: close\r\n\r\n"
        )


class DependencyContractsTest(unittest.TestCase):
    """Keep the dependency APIs that the evaluation code expects."""

    def test_deepeval_evaluate_is_callable(self) -> None:
        self.assertTrue(callable(evaluate))

    @patch("auto_evaluation.src.models.gemini.genai.Client")
    def test_gemini_model_keeps_its_name(self, _client: object) -> None:
        model = GoogleGeminiLangChain(model_name="gemini-test")

        self.assertEqual(model.get_model_name(), "gemini-test")

    @patch("auto_evaluation.src.models.gemini.genai.Client")
    def test_gemini_model_retries_temporary_unavailability(
        self, client: MagicMock
    ) -> None:
        class TemporaryFailureModels:
            def __init__(self) -> None:
                self.attempts = 0

            async def generate_content(self, **_kwargs: object) -> object:
                self.attempts += 1
                if self.attempts < 3:
                    raise errors.ServerError(
                        503,
                        {"error": {"status": "UNAVAILABLE"}},
                    )
                return SimpleNamespace(text="recovered")

        models = TemporaryFailureModels()
        client.return_value = SimpleNamespace(
            models=models,
            aio=SimpleNamespace(models=models),
        )
        model = GoogleGeminiLangChain(model_name="gemini-test")

        with patch(
            "asyncio.sleep",
            new_callable=AsyncMock,
        ):
            response = asyncio.run(model.a_generate("test"))

        self.assertEqual(response, "recovered")
        self.assertEqual(models.attempts, 3)

    def test_evaluation_query_uses_single_slash_path(self) -> None:
        server = socketserver.ThreadingTCPServer(("127.0.0.1", 0), QueryHandler)
        thread = threading.Thread(target=server.serve_forever)
        thread.start()
        self.addCleanup(thread.join)
        self.addCleanup(server.server_close)
        self.addCleanup(server.shutdown)

        harness = object.__new__(EvaluationHarness)
        harness.base_url = f"http://127.0.0.1:{server.server_address[1]}"
        harness.reranker_base_url = ""

        with patch("auto_evaluation.eval_main.time.sleep"):
            response, _ = harness.query("agent-retriever", "test")

        self.assertEqual(response["response"], "ok")
        self.assertEqual(QueryHandler.path_seen, "/conversations/agent-retriever")

    def test_evaluation_query_raises_for_backend_failure(self) -> None:
        server = socketserver.ThreadingTCPServer(
            ("127.0.0.1", 0), UnavailableQueryHandler
        )
        thread = threading.Thread(target=server.serve_forever)
        thread.start()
        self.addCleanup(thread.join)
        self.addCleanup(server.server_close)
        self.addCleanup(server.shutdown)

        harness = object.__new__(EvaluationHarness)
        harness.base_url = f"http://127.0.0.1:{server.server_address[1]}"
        harness.reranker_base_url = ""

        with patch("auto_evaluation.eval_main.time.sleep"):
            with self.assertRaises(requests.HTTPError):
                harness.query("agent-retriever", "test")


if __name__ == "__main__":
    unittest.main()
