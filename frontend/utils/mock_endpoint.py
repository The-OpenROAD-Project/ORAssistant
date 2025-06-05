from flask import Flask, request, jsonify, Response
from typing import Any

app = Flask(__name__)


@app.route("/chains/listAll")
def list_all_chains() -> Response:
    """
    Endpoint returning a list of available chains.

    Returns:
    - A JSON response containing a list of available chains.
    """
    return jsonify(["/chains/mock"])


@app.route("/graphs/agent-retriever", methods=["POST"])
def chat_app() -> Response:
    """
    Endpoint to handle chat requests.

    Returns:
    - A JSON response containing the Mock Endpoint API response, sources, and context based on user input.
    """
    data: dict[str, Any] = request.get_json()
    user_query: str = data.get("query", "")
    list_sources: bool = data.get("list_sources", True)
    list_context: bool = data.get("list_context", True)

    dummy_context_sources = [
        {"source": "https://mocksource1.com", "context": "This is Mock Context 1"},
        {"source": "https://mocksource2.com", "context": "This is Mock Context 2"},
    ]
    if not list_sources:
        # drop the source keys
        dummy_context_sources = [
            {"source": "", "context": cs["context"]} for cs in dummy_context_sources
        ]
    if not list_context:
        # drop the context keys
        dummy_context_sources = [
            {"source": cs["source"], "context": ""} for cs in dummy_context_sources
        ]
    response = {
        "response": f"This is a mock response to your query: '{user_query}'",
        "context_sources": dummy_context_sources,
    }

    return jsonify(response)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8001)
