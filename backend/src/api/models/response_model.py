from typing import Optional
from pydantic import BaseModel
from datetime import datetime


class UserInput(BaseModel):
    query: str
    list_sources: bool = False
    list_context: bool = False
    conversation_id: Optional[str] = None


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


class MessageResponse(BaseModel):
    id: int
    conversation_id: str
    role: str
    content: str
    context_sources: Optional[dict] = None
    tools: Optional[list] = None
    created_at: datetime

    class Config:
        from_attributes = True


class ConversationResponse(BaseModel):
    id: str
    title: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    messages: list[MessageResponse] = []

    class Config:
        from_attributes = True


class ConversationListResponse(BaseModel):
    id: str
    title: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
