from typing import Optional
from pydantic import BaseModel, ConfigDict
from datetime import datetime
from uuid import UUID


class UserInput(BaseModel):
    query: str
    list_sources: bool = False
    list_context: bool = False
    conversation_uuid: Optional[UUID] = None


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


class MessageResponse(BaseModel):
    uuid: UUID
    conversation_uuid: UUID
    role: str
    content: str
    context_sources: Optional[dict] = None
    tools: Optional[list] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ConversationResponse(BaseModel):
    uuid: UUID
    title: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    messages: list[MessageResponse] = []

    model_config = ConfigDict(from_attributes=True)


class ConversationListResponse(BaseModel):
    uuid: UUID
    title: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
