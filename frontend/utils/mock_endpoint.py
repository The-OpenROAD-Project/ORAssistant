from flask import Flask, request, jsonify, Response
from typing import Dict, Any

app = Flask(__name__)


@app.route("/chatApp", methods=["POST"])
def chat_app() -> Response:
    """
    Endpoint to handle chat requests.

    Returns:
    - A JSON response containing the Mock Endpoint API response, sources, and context based on user input.
    """
    data: Dict[str, Any] = request.get_json()
    user_query: str = data.get("query", "")
    list_sources: bool = data.get("listSources", False)
    list_context: bool = data.get("listContext", False)

    response_data: Dict[str, str] = {
        "response": f"Response to your query: '{user_query}'",
        "sources": (
            "{'https://openroad-flow-scripts.readthedocs.io/en/latest/mainREADME.html', "
            "'https://openroad-flow-scripts.readthedocs.io/en/latest/user/BuildWithWSL.html', "
            "'https://openroad.readthedocs.io/en/latest/user/MessagesFinal.html', "
            "'https://openroad-flow-scripts.readthedocs.io/en/latest/tutorials/FlowTutorial.html'}"
        )
        if list_sources
        else "",
        "context": "Mock context data" if list_context else "",
    }

    return jsonify(response_data)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000)
