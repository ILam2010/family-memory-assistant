"""Where photo FILES live on disk. Metadata lives in the database, not here.

"""

import uuid
from datetime import datetime, timezone
from pathlib import Path

from app.config import settings


def new_photo_location(extension: str = ".jpg") -> tuple[str, Path]:
    """Return (relative_path_for_database, absolute_path_on_disk) for a new photo."""
    year = datetime.now(timezone.utc).strftime("%Y")
    relative = f"{year}/{uuid.uuid4().hex}{extension}"
    absolute = settings.photos_dir / relative
    absolute.parent.mkdir(parents=True, exist_ok=True)
    return relative, absolute


def resolve_photo_path(relative_path: str) -> Path:
    """Turn a stored relative path into a real path, refusing anything that
    would escape the photos folder (path traversal protection)."""
    base = settings.photos_dir.resolve()
    path = (base / relative_path).resolve()
    if not path.is_relative_to(base):
        raise ValueError("Invalid photo path")
    return path