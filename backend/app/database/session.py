"""Database connection and sessions."""

import sqlite3
from pathlib import Path

from sqlalchemy import create_engine, event
from sqlalchemy.engine import Engine
from sqlalchemy.orm import sessionmaker

from app.config import PROJECT_ROOT, settings
from app.database.models import Base


def _resolve_url(url: str) -> str:
    """Make a relative sqlite path relative to the PROJECT ROOT, not the
    folder you happen to run the command from."""
    prefix = "sqlite:///"
    if url.startswith(prefix):
        path = Path(url[len(prefix):])
        if not path.is_absolute():
            path = (PROJECT_ROOT / path).resolve()
        path.parent.mkdir(parents=True, exist_ok=True)
        return prefix + path.as_posix()
    return url


@event.listens_for(Engine, "connect")
def _enable_sqlite_foreign_keys(dbapi_connection, connection_record):
    """SQLite ignores foreign keys unless you switch them on."""
    if isinstance(dbapi_connection, sqlite3.Connection):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()


engine = create_engine(_resolve_url(settings.database_url))
SessionLocal = sessionmaker(bind=engine, expire_on_commit=False)


def init_db() -> None:
    """Create any missing tables."""
    Base.metadata.create_all(engine)