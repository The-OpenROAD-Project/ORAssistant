"""Vertex AI settings for the Gemini chat models."""

from typing import Any

# Vertex AI serves Gemini 3 models from the global endpoint. Regional
# endpoints such as us-central1 answer 404 "Publisher model ... not found".
_GLOBAL_ONLY_PREFIX = "gemini-3"


def vertex_chat_kwargs(model_name: str) -> dict[str, Any]:
    """Return ChatVertexAI arguments that select a location serving the model.

    Other models keep the location from the Vertex AI configuration.
    """
    kwargs: dict[str, Any] = {"model_name": model_name}
    if model_name.startswith(_GLOBAL_ONLY_PREFIX):
        kwargs["location"] = "global"
    return kwargs
