from flask import Flask, request, jsonify, Response
from typing import Any

app = Flask(__name__)


@app.route('/chains/listAll')
def list_all_chains() -> Response:
    """
    Endpoint returning a list of available chains.

    Returns:
    - A JSON response containing a list of available chains.
    """
    return jsonify(['/chains/mock'])


@app.route('/chains/mock', methods=['POST'])
def chat_app() -> Response:
    """
    Endpoint to handle chat requests.

    Returns:
    - A JSON response containing the Mock Endpoint API response, sources, and context based on user input.
    """
    data: dict[str, Any] = request.get_json()
    user_query: str = data.get('query', '')
    list_sources: bool = data.get('list_sources', False)
    list_context: bool = data.get('list_context', False)

    response = {
        'response': f"This is a mock response to your query: '{user_query}'",
        'sources': [
            'https://mocksource1.com',
            'https://mocksource2.com',
            'https://mocksource3.com',
        ]
        if list_sources
        else [],
        'context': ['This is Mock Context'] if list_context else [],
    }

    return jsonify(response)


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000)
