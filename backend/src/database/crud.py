from typing import Optional
from sqlalchemy.orm import Session
from sqlalchemy import desc
from .models import Conversation, Message
from uuid import UUID


def create_conversation(
    db: Session, conversation_uuid: Optional[UUID] = None, title: Optional[str] = None
) -> Conversation:
    conversation = (
        Conversation(uuid=conversation_uuid, title=title)
        if conversation_uuid
        else Conversation(title=title)
    )
    db.add(conversation)
    db.commit()
    db.refresh(conversation)
    return conversation


def get_conversation(db: Session, conversation_uuid: UUID) -> Optional[Conversation]:
    return db.query(Conversation).filter(Conversation.uuid == conversation_uuid).first()


def get_or_create_conversation(
    db: Session, conversation_uuid: Optional[UUID] = None, title: Optional[str] = None
) -> Conversation:
    if conversation_uuid:
        conversation = get_conversation(db, conversation_uuid)
        if conversation:
            return conversation
    return create_conversation(db, conversation_uuid, title)


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
    db: Session, conversation_uuid: UUID, title: str
) -> Optional[Conversation]:
    conversation = get_conversation(db, conversation_uuid)
    if conversation:
        conversation.title = title
        db.commit()
        db.refresh(conversation)
    return conversation


def delete_conversation(db: Session, conversation_uuid: UUID) -> bool:
    conversation = get_conversation(db, conversation_uuid)
    if conversation:
        db.delete(conversation)
        db.commit()
        return True
    return False


def create_message(
    db: Session,
    conversation_uuid: UUID,
    role: str,
    content: str,
    context_sources: Optional[dict] = None,
    tools: Optional[list] = None,
) -> Message:
    message = Message(
        conversation_uuid=conversation_uuid,
        role=role,
        content=content,
        context_sources=context_sources,
        tools=tools,
    )
    db.add(message)
    db.commit()
    db.refresh(message)
    return message


def get_message(db: Session, message_id: UUID) -> Optional[Message]:
    return db.query(Message).filter(Message.uuid == message_id).first()


def get_conversation_messages(
    db: Session, conversation_uuid: UUID, skip: int = 0, limit: int = 100
) -> list[Message]:
    return (
        db.query(Message)
        .filter(Message.conversation_uuid == conversation_uuid)
        .order_by(Message.created_at)
        .offset(skip)
        .limit(limit)
        .all()
    )


def delete_message(db: Session, message_id: UUID) -> bool:
    message = get_message(db, message_id)
    if message:
        db.delete(message)
        db.commit()
        return True
    return False


def get_conversation_history(
    db: Session, conversation_uuid: UUID
) -> list[dict[str, str]]:
    messages = get_conversation_messages(db, conversation_uuid)
    history = []
    current_pair: dict[str, str] = {}

    for message in messages:
        if message.role == "user":
            if current_pair:
                history.append(current_pair)
            current_pair = {"User": message.content}
        elif message.role == "assistant" and current_pair:
            current_pair["AI"] = message.content
            history.append(current_pair)
            current_pair = {}

    if current_pair:
        history.append(current_pair)

    return history
