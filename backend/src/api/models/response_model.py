from pydantic import BaseModel


class UserInput(BaseModel):
    query: str
    chat_history: list[dict[str, str]] = []
    list_sources: bool = False
    list_context: bool = False


class ChatResponse(BaseModel):
    response: str
    sources: list[str] = []
    context: list[str] = []
    tool: str


class ChatToolResponse(BaseModel):
    response: str
    sources: list[str] = []
    context: list[str] = []
    tool: str
