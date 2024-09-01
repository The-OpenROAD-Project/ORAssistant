import requests
import os
from typing import Any

API_BASE_URL = os.getenv('CHAT_ENDPOINT', 'http://localhost:8000')
HEADERS = {'accept': 'application/json', 'Content-Type': 'application/json'}

def get_responses(
    questions: list[str],
    progress: Any,
    status_text: Any,
    current_question_text: Any,
    endpoint: str = '/graphs/agent-retriever'
) -> list[str]:
    """
    Fetch responses from AI for a list of questions.

    Args:
    - questions (list[str]): List of questions to query the AI.
    - progress (Any): Streamlit progress bar object.
    - status_text (Any): Streamlit text object for status updates.
    - current_question_text (Any): Streamlit text object for current question display.
    - endpoint (str): Optional endpoint to use for the API call. Defaults to '/graphs/agent-retriever'.

    Returns:
    - list[str]: List of responses from the AI combined with sources.
    """
    responses = []

    for i, question in enumerate(questions):
        current_question_text.text(f'Current question: {question}')
        payload = {'query': question, 'list_sources': True}

        try:
            url = f'{API_BASE_URL}{endpoint}'
            response = requests.post(url, headers=HEADERS, json=payload)
            response.raise_for_status()

            try:
                data = response.json()
                response_text = data.get('response', 'No response')

                sources = data.get('sources', [])
                formatted_sources = '\n'.join(sources)

                combined_response_sources = (
                    f'{response_text}\nSources:\n{formatted_sources}'
                )
                responses.append(combined_response_sources)
            except ValueError:
                responses.append('Invalid JSON response')
        except requests.exceptions.RequestException as err:
            responses.append(str(err))

        progress.progress((i + 1) / len(questions))
        status_text.text(f'Processing {i + 1}/{len(questions)}...')

    return responses