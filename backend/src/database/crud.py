from typing import Optional
from sqlalchemy.orm import Session
from sqlalchemy import desc
from .models import Conversation, Message
import uuid


def create_conversation(
    db: Session, conversation_id: Optional[str] = None, title: Optional[str] = None
) -> Conversation:
    if conversation_id is None:
        conversation_id = str(uuid.uuid4())
    conversation = Conversation(id=conversation_id, title=title)
    db.add(conversation)
    db.commit()
    db.refresh(conversation)
    return conversation


def get_conversation(db: Session, conversation_id: str) -> Optional[Conversation]:
    return db.query(Conversation).filter(Conversation.id == conversation_id).first()


def get_or_create_conversation(
    db: Session, conversation_id: Optional[str] = None, title: Optional[str] = None
) -> Conversation:
    if conversation_id:
        conversation = get_conversation(db, conversation_id)
        if conversation:
            return conversation
    return create_conversation(db, conversation_id, title)


def get_all_conversations(
    db: Session, skip: int = 0, limit: int = 100
) -> list[Conversation]:
    return (
        db.query(Conversation)
        .order_by(desc(Conversation.updated_at))
        .offset(skip)
        .limit(limit)
        .all()
    )


def update_conversation_title(
    db: Session, conversation_id: str, title: str
) -> Optional[Conversation]:
    conversation = get_conversation(db, conversation_id)
    if conversation:
        conversation.title = title
        db.commit()
        db.refresh(conversation)
    return conversation


def delete_conversation(db: Session, conversation_id: str) -> bool:
    conversation = get_conversation(db, conversation_id)
    if conversation:
        db.delete(conversation)
        db.commit()
        return True
    return False


def create_message(
    db: Session,
    conversation_id: str,
    role: str,
    content: str,
    context_sources: Optional[dict] = None,
    tools: Optional[list] = None,
) -> Message:
    message = Message(
        conversation_id=conversation_id,
        role=role,
        content=content,
        context_sources=context_sources,
        tools=tools,
    )
    db.add(message)
    db.commit()
    db.refresh(message)
    return message


def get_message(db: Session, message_id: int) -> Optional[Message]:
    return db.query(Message).filter(Message.id == message_id).first()


def get_conversation_messages(
    db: Session, conversation_id: str, skip: int = 0, limit: int = 100
) -> list[Message]:
    return (
        db.query(Message)
        .filter(Message.conversation_id == conversation_id)
        .order_by(Message.created_at)
        .offset(skip)
        .limit(limit)
        .all()
    )


def delete_message(db: Session, message_id: int) -> bool:
    message = get_message(db, message_id)
    if message:
        db.delete(message)
        db.commit()
        return True
    return False


def get_conversation_history(db: Session, conversation_id: str) -> list[dict[str, str]]:
    messages = get_conversation_messages(db, conversation_id)
    history = []
    current_pair: dict[str, str] = {}

    for message in messages:
        if message.role == "user":
            current_pair = {"User": message.content}
        elif message.role == "assistant" and current_pair:
            current_pair["AI"] = message.content
            history.append(current_pair)
            current_pair = {}

    return history
