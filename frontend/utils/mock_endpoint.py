from fastapi import FastAPI
from pydantic import BaseModel
from typing import List


app = FastAPI()


class ChatRequest(BaseModel):
    query: str
    list_sources: bool = True
    list_context: bool = True


class ContextSource(BaseModel):
    source: str
    context: str


class ChatResponse(BaseModel):
    response: str
    context_sources: List[ContextSource]


@app.get("/chains/listAll")
def list_all_chains() -> List[str]:
    """
    Endpoint returning a list of available chains.

    Returns:
    - A JSON response containing a list of available chains.
    """
    return ["/chains/mock"]


@app.post("/conversations/agent-retriever", response_model=ChatResponse)
def chat_app(request: ChatRequest) -> ChatResponse:
    """
    Endpoint to handle chat requests.

    Returns:
    - A JSON response containing the Mock Endpoint API response, sources, and context based on user input.
    """
    user_query = request.query
    list_sources = request.list_sources
    list_context = request.list_context

    dummy_context_sources = [
        ContextSource(
            source="https://mocksource1.com", context="This is Mock Context 1"
        ),
        ContextSource(
            source="https://mocksource2.com", context="This is Mock Context 2"
        ),
    ]
    if not list_sources:
        # drop the source keys
        dummy_context_sources = [
            ContextSource(source="", context=cs.context) for cs in dummy_context_sources
        ]
    if not list_context:
        # drop the context keys
        dummy_context_sources = [
            ContextSource(source=cs.source, context="") for cs in dummy_context_sources
        ]

    return ChatResponse(
        response=f"This is a mock response to your query: '{user_query}'",
        context_sources=dummy_context_sources,
    )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8001)
