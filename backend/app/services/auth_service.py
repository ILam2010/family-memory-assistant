"""Authorization logic: who is allowed to use the family assistant?

This file knows nothing about Telegram. It only answers one question:
"Is this Telegram user ID an approved family member, and with what role?"

"""

from dataclasses import dataclass
from enum import Enum

from app.config import settings


class Role(str, Enum):
    ADMIN = "ADMIN"
    MEMBER = "MEMBER"


@dataclass(frozen=True)
class FamilyMember:
    telegram_user_id: int
    role: Role


def get_member(telegram_user_id: int) -> FamilyMember | None:
    """Return the family member for this Telegram ID, or None if not approved."""
    if telegram_user_id in settings.admin_ids:
        return FamilyMember(telegram_user_id, Role.ADMIN)
    if telegram_user_id in settings.member_ids:
        return FamilyMember(telegram_user_id, Role.MEMBER)
    return None


def is_admin(member: FamilyMember | None) -> bool:
    return member is not None and member.role == Role.ADMIN