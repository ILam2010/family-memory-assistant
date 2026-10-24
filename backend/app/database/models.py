"""Database table definitions (SQLAlchemy models)."""

import enum
from datetime import datetime, timezone

from sqlalchemy import BigInteger, DateTime, Enum, ForeignKey, SmallInteger, String, Text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


def _now() -> datetime:
    return datetime.now(timezone.utc)


class Base(DeclarativeBase):
    """Every model inherits from this; it keeps track of all my tables."""


class Role(str, enum.Enum):
    ADMIN = "ADMIN"
    MEMBER = "MEMBER"


class MemberStatus(str, enum.Enum):
    ACTIVE = "ACTIVE"
    PENDING = "PENDING"
    DISABLED = "DISABLED"


class FamilyMember(Base):
    __tablename__ = "family_members"

    id: Mapped[int] = mapped_column(primary_key=True)
    telegram_user_id: Mapped[int] = mapped_column(BigInteger, unique=True, index=True)
    name: Mapped[str | None] = mapped_column(String(100))
    family_relation: Mapped[str | None] = mapped_column(String(50))
    role: Mapped[Role] = mapped_column(Enum(Role), default=Role.MEMBER)
    status: Mapped[MemberStatus] = mapped_column(
        Enum(MemberStatus), default=MemberStatus.ACTIVE
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)

    photos: Mapped[list["Photo"]] = relationship(back_populates="uploader")


class Event(Base):
    __tablename__ = "events"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(200))
    # Partial date: year only, year+month, or a full day. All optional.
    year: Mapped[int | None] = mapped_column(SmallInteger, index=True)
    month: Mapped[int | None] = mapped_column(SmallInteger)
    day: Mapped[int | None] = mapped_column(SmallInteger)
    location: Mapped[str | None] = mapped_column(String(200))
    description: Mapped[str | None] = mapped_column(Text)

    photos: Mapped[list["Photo"]] = relationship(back_populates="event")


class Photo(Base):
    __tablename__ = "photos"

    id: Mapped[int] = mapped_column(primary_key=True)
    uploader_id: Mapped[int] = mapped_column(ForeignKey("family_members.id"))
    event_id: Mapped[int | None] = mapped_column(ForeignKey("events.id"))
    file_path: Mapped[str] = mapped_column(String(500))
    telegram_file_id: Mapped[str | None] = mapped_column(String(300))
    description: Mapped[str | None] = mapped_column(Text)
    # Partial date of when the photo was taken. All optional.
    photo_year: Mapped[int | None] = mapped_column(SmallInteger, index=True)
    photo_month: Mapped[int | None] = mapped_column(SmallInteger)
    photo_day: Mapped[int | None] = mapped_column(SmallInteger)
    location: Mapped[str | None] = mapped_column(String(200))
    people: Mapped[str | None] = mapped_column(Text)
    uploaded_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)

    uploader: Mapped["FamilyMember"] = relationship(back_populates="photos")
    event: Mapped["Event | None"] = relationship(back_populates="photos")