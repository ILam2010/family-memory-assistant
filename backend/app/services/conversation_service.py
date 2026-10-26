"""Conversation history: used ONLY to understand follow-up questions."""

from datetime import datetime, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database.models import Conversation, Message, MessageRole


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _as_utc(value: datetime) -> datetime:
    
    return value if value.tzinfo else value.replace(tzinfo=timezone.utc)


def get_or_create_active(session: Session, member_id: int, ttl_minutes: int) -> Conversation:
    """The member's current conversation, or a fresh one if it has gone quiet."""
    latest = session.execute(
        select(Conversation)
        .where(Conversation.member_id == member_id)
        .order_by(Conversation.updated_at.desc())
        .limit(1)
    ).scalar_one_or_none()

    if latest is not None and _now() - _as_utc(latest.updated_at) <= timedelta(minutes=ttl_minutes):
        return latest

    conversation = Conversation(member_id=member_id)
    session.add(conversation)
    session.commit()
    return conversation


def add_message(session: Session, conversation_id: int, role: MessageRole, text: str) -> None:
    session.add(Message(conversation_id=conversation_id, role=role, text=text[:4000]))
    conversation = session.get(Conversation, conversation_id)
    if conversation is not None:
        conversation.updated_at = _now()
    session.commit()


def recent_history(session: Session, conversation_id: int, limit: int) -> list[tuple[str, str]]:
    """The last `limit` messages, oldest first, as (role, text) pairs."""
    messages = list(
        session.execute(
            select(Message)
            .where(Message.conversation_id == conversation_id)
            .order_by(Message.id.desc())
            .limit(limit)
        ).scalars()
    )
    messages.reverse()
    return [(message.role.value, message.text) for message in messages]


def clear_history(session: Session, member_id: int) -> int:
    """Delete all of one member's conversations. Returns how many were deleted."""
    conversations = list(
        session.execute(
            select(Conversation).where(Conversation.member_id == member_id)
        ).scalars()
    )
    for conversation in conversations:
        session.delete(conversation)
    session.commit()
    return len(conversations)