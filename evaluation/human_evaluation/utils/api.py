import requests
import os
import ast
from typing import List, Any

API_URL = os.getenv("CHAT_ENDPOINT", "http://localhost:8000/chatApp")
HEADERS = {"accept": "application/json", "Content-Type": "application/json"}


def get_responses(
    questions: List[str], progress: Any, status_text: Any, current_question_text: Any
) -> List[str]:
    """
    Fetch responses from AI for a list of questions.

    Args:
    - questions (List[str]): List of questions to query the AI.
    - progress (Any): Streamlit progress bar object.
    - status_text (Any): Streamlit text object for status updates.
    - current_question_text (Any): Streamlit text object for current question display.

    Returns:
    - List[str]: List of responses from the AI combined with sources.
    """
    responses = []

    for i, question in enumerate(questions):
        current_question_text.text(f"Current question: {question}")
        payload = {"query": question, "listSources": True}

        try:
            response = requests.post(API_URL, headers=HEADERS, json=payload)
            response.raise_for_status()

            try:
                data = response.json()
                response_text = data.get("response", "No response")

                sources_str = data.get("sources", "")
                sources = ast.literal_eval(sources_str) if sources_str else set()
                formatted_sources = "\n".join(sources)

                combined_response_sources = (
                    f"{response_text}\nSources:\n{formatted_sources}"
                )
                responses.append(combined_response_sources)
            except ValueError:
                responses.append("Invalid JSON response")
        except requests.exceptions.RequestException as err:
            responses.append(str(err))

        progress.progress((i + 1) / len(questions))
        status_text.text(f"Processing {i + 1}/{len(questions)}...")

    return responses
