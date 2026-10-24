"""Authorization logic: who is allowed to use the family assistant?

This file knows nothing about Telegram. It only answers:
"Is this Telegram user ID an active family member, and with what role?"
"""

from dataclasses import dataclass

from app.database.models import MemberStatus, Role
from app.database.session import SessionLocal
from app.services import member_service


@dataclass(frozen=True)
class AuthenticatedMember:
    telegram_user_id: int
    name: str | None
    role: Role


def get_member(telegram_user_id: int) -> AuthenticatedMember | None:
    """Return the member if approved AND active, otherwise None (= denied)."""
    with SessionLocal() as session:
        member = member_service.get_by_telegram_id(session, telegram_user_id)
        if member is None or member.status != MemberStatus.ACTIVE:
            return None
        return AuthenticatedMember(member.telegram_user_id, member.name, member.role)


def is_admin(member: AuthenticatedMember | None) -> bool:
    return member is not None and member.role == Role.ADMIN