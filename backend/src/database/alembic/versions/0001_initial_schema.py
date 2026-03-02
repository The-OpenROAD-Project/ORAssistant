"""Initial schema

Revision ID: 0001
Revises:
Create Date: 2026-03-01

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "0001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "conversations",
        sa.Column("uuid", sa.Uuid(), primary_key=True),
        sa.Column("title", sa.String(500), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )

    op.create_table(
        "messages",
        sa.Column("uuid", sa.Uuid(), primary_key=True),
        sa.Column(
            "conversation_uuid",
            sa.Uuid(),
            sa.ForeignKey("conversations.uuid", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("role", sa.String(50), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("context_sources", sa.JSON(), nullable=True),
        sa.Column("tools", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )

    op.create_index(
        "ix_messages_conversation_uuid",
        "messages",
        ["conversation_uuid"],
    )


def downgrade() -> None:
    op.drop_index("ix_messages_conversation_uuid", table_name="messages")
    op.drop_table("messages")
    op.drop_table("conversations")
