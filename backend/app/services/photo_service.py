"""Create and read Photo records in the database."""

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database.models import Event, Photo
from app.services.dates import format_partial_date, parse_partial_date


def create_photo(
    session: Session,
    uploader_id: int,
    file_path: str,
    telegram_file_id: str | None = None,
    description: str | None = None,
) -> Photo:
    photo = Photo(
        uploader_id=uploader_id,
        file_path=file_path,
        telegram_file_id=telegram_file_id,
        description=description,
    )
    session.add(photo)
    session.commit()
    return photo


def get_photo(session: Session, photo_id: int) -> Photo | None:
    return session.get(Photo, photo_id)


def set_description(
    session: Session, photo_id: int, uploader_id: int, description: str
) -> bool:
    """Set a photo's description. Only the uploader may do this.
    Returns True if updated, False if the photo doesn't exist or isn't theirs."""
    photo = session.get(Photo, photo_id)
    if photo is None or photo.uploader_id != uploader_id:
        return False
    photo.description = description
    session.commit()
    return True


def list_by_uploader(session: Session, uploader_id: int) -> list[Photo]:
    stmt = select(Photo).where(Photo.uploader_id == uploader_id).order_by(Photo.id)
    return list(session.execute(stmt).scalars())


EDITABLE_FIELDS = ("description", "people", "location", "date", "event")


def edit_photo(
    session: Session,
    photo_id: int,
    editor_member_id: int,
    editor_is_admin: bool,
    field: str,
    value: str,
) -> Photo:
    """Change one field of a photo. Raises:
    LookupError("photo") / LookupError("event"), PermissionError, ValueError(message)."""
    photo = session.get(Photo, photo_id)
    if photo is None:
        raise LookupError("photo")
    if photo.uploader_id != editor_member_id and not editor_is_admin:
        raise PermissionError("not the uploader")

    value = value.strip()
    if field == "description":
        photo.description = value[:2000] or None
    elif field == "people":
        photo.people = value[:500] or None
    elif field == "location":
        photo.location = value[:200] or None
    elif field == "date":
        if value.lower() in ("none", "clear"):
            photo.photo_year = photo.photo_month = photo.photo_day = None
        else:
            photo.photo_year, photo.photo_month, photo.photo_day = parse_partial_date(value)
    elif field == "event":
        if value.lower() == "none":
            photo.event_id = None
        elif value.isdigit():
            event = session.get(Event, int(value))
            if event is None:
                raise LookupError("event")
            photo.event_id = event.id
        else:
            raise ValueError("Use an event number from /events, or the word none.")
    else:
        raise ValueError("Unknown field. Choose one of: " + ", ".join(EDITABLE_FIELDS))

    session.commit()
    return photo


def photo_summary(photo: Photo) -> str:
    """Human-readable text for a photo (must be called while the session is open)."""
    lines = []
    if photo.description:
        lines.append(photo.description)
    if photo.event:
        lines.append(f"Event: {photo.event.name}")
    if photo.people:
        lines.append(f"People: {photo.people}")
    if photo.location:
        lines.append(f"Location: {photo.location}")
    when = format_partial_date(photo.photo_year, photo.photo_month, photo.photo_day)
    if when:
        lines.append(f"Date: {when}")
    return "\n".join(lines)