"""Create and read family events."""

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.database.models import Event, Photo


def create_event(
    session: Session,
    name: str,
    year: int | None = None,
    month: int | None = None,
    day: int | None = None,
    location: str | None = None,
    description: str | None = None,
) -> Event:
    event = Event(
        name=name, year=year, month=month, day=day,
        location=location, description=description,
    )
    session.add(event)
    session.commit()
    return event


def get_event(session: Session, event_id: int) -> Event | None:
    return session.get(Event, event_id)


def list_events_with_counts(session: Session) -> list[tuple[Event, int]]:
    """Every event together with how many photos it has."""
    stmt = (
        select(Event, func.count(Photo.id))
        .outerjoin(Photo, Photo.event_id == Event.id)
        .group_by(Event.id)
        .order_by(Event.id)
    )
    return [(event, count) for event, count in session.execute(stmt).all()]