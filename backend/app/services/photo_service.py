"""Create and read Photo records in the database."""

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database.models import Photo


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