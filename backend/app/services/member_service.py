"""Create / read / update family members in the database."""

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import settings
from app.database.models import FamilyMember, MemberStatus, Role


def create_member(
    session: Session,
    telegram_user_id: int,
    name: str | None = None,
    family_relation: str | None = None,
    role: Role = Role.MEMBER,
) -> FamilyMember:
    if get_by_telegram_id(session, telegram_user_id) is not None:
        raise ValueError("Member already exists")
    member = FamilyMember(
        telegram_user_id=telegram_user_id,
        name=name,
        family_relation=family_relation,
        role=role,
    )
    session.add(member)
    session.commit()
    return member


def get_by_telegram_id(session: Session, telegram_user_id: int) -> FamilyMember | None:
    stmt = select(FamilyMember).where(FamilyMember.telegram_user_id == telegram_user_id)
    return session.execute(stmt).scalar_one_or_none()


def list_members(session: Session) -> list[FamilyMember]:
    return list(session.execute(select(FamilyMember).order_by(FamilyMember.id)).scalars())


def set_role(session: Session, member: FamilyMember, role: Role) -> None:
    member.role = role
    session.commit()


def set_status(session: Session, member: FamilyMember, status: MemberStatus) -> None:
    member.status = status
    session.commit()


def seed_from_env(session: Session) -> None:
    """Make sure IDs listed in .env exist in the database.

    .env is now only a bootstrap: it guarantees the first admin can get in.
    After that, the database is the source of truth.
    """
    for telegram_id in settings.admin_ids:
        if get_by_telegram_id(session, telegram_id) is None:
            create_member(session, telegram_id, role=Role.ADMIN)
    for telegram_id in settings.member_ids:
        if get_by_telegram_id(session, telegram_id) is None:
            create_member(session, telegram_id, role=Role.MEMBER)


def set_name(session: Session, member_id: int, name: str) -> None:
    member = session.get(FamilyMember, member_id)
    if member is not None:
        member.name = name
        session.commit()