"""Test conversation storage with NO Gemini calls. Uses a temporary in-memory database.
"""

from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

from app.database.models import Base, Conversation, FamilyMember, MessageRole
from app.services import conversation_service as cs

engine = create_engine("sqlite://")
Base.metadata.create_all(engine)

with Session(engine) as session:
    member = FamilyMember(telegram_user_id=1, name="Test")
    session.add(member)
    session.commit()

    first = cs.get_or_create_active(session, member.id, ttl_minutes=30)
    cs.add_message(session, first.id, MessageRole.USER, "When did we visit Hawassa?")
    cs.add_message(session, first.id, MessageRole.BOT, "In December 2023.")

    again = cs.get_or_create_active(session, member.id, ttl_minutes=30)
    print("Same conversation within the time limit:", again.id == first.id)
    print("History (oldest first):", cs.recent_history(session, first.id, 6))

    expired = cs.get_or_create_active(session, member.id, ttl_minutes=0)
    print("New conversation once expired:", expired.id != first.id)

    deleted = cs.clear_history(session, member.id)
    remaining = len(session.execute(select(Conversation)).scalars().all())
    print(f"/forget deleted {deleted} conversation(s); {remaining} left")