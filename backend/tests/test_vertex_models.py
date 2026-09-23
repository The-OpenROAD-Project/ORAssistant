import pytest

from src.tools.vertex_models import vertex_chat_kwargs


def test_gemini_3_uses_the_global_endpoint() -> None:
    assert vertex_chat_kwargs("gemini-3.6-flash") == {
        "model_name": "gemini-3.6-flash",
        "location": "global",
    }


@pytest.mark.parametrize("model_name", ["gemini-2.5-flash", "gemini-2.5-pro"])
def test_older_models_keep_the_configured_location(model_name: str) -> None:
    assert vertex_chat_kwargs(model_name) == {"model_name": model_name}
