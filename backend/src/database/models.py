from datetime import datetime, timezone
from typing import Optional
from sqlalchemy import DateTime, ForeignKey, String, Text, JSON, Uuid
from sqlalchemy.orm import DeclarativeBase, relationship, Mapped, mapped_column
from uuid import uuid4, UUID


class Base(DeclarativeBase):
    pass


class Conversation(Base):
    __tablename__ = "conversations"

    uuid: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    title: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    messages: Mapped[list["Message"]] = relationship(
        "Message",
        back_populates="conversation",
        cascade="all, delete-orphan",
        order_by="Message.created_at",
    )

    def __repr__(self) -> str:
        return f"<Conversation(uuid={self.uuid}, title={self.title})>"


class Message(Base):
    __tablename__ = "messages"

    uuid: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    conversation_uuid: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("conversations.uuid", ondelete="CASCADE"), index=True
    )
    role: Mapped[str] = mapped_column(String(50))
    content: Mapped[str] = mapped_column(Text)
    context_sources: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    tools: Mapped[Optional[list]] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )

    conversation: Mapped["Conversation"] = relationship(
        "Conversation", back_populates="messages"
    )

    def __repr__(self) -> str:
        return f"<Message(uuid={self.uuid}, conversation_uuid={self.conversation_uuid}, role={self.role})>"
