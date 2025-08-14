from pydantic import BaseModel


class UserInput(BaseModel):
    query: str
    chat_history: list[dict[str, str]] = []
    list_sources: bool = False
    list_context: bool = False


class ContextSource(BaseModel):
    source: str = ""
    context: str = ""


class SuggestedQuestions(BaseModel):
    suggested_questions: list[str]


class SuggestedQuestionInput(BaseModel):
    latest_question: str
    assistant_answer: str


class ChatResponse(BaseModel):
    response: str
    context_sources: list[ContextSource] = []
    tools: list[str] = []


class ChatToolResponse(BaseModel):
    response: str
    sources: list[str] = []
    context: list[str] = []
    tools: list[str] = []
