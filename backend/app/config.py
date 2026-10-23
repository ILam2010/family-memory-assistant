"""Central place where the app reads its settings.

Every other file imports settings from here, instead of reading
environment variables on its own.
"""

import os
from pathlib import Path

from dotenv import load_dotenv

# config.py is at: family-memory-assistant/backend/app/config.py
# parents[0] = app, parents[1] = backend, parents[2] = project root
PROJECT_ROOT = Path(__file__).resolve().parents[2]

# Read the .env file from the project root into environment variables.
load_dotenv(PROJECT_ROOT / ".env")


class Settings:
    """Holds all configuration values in one object."""

    telegram_bot_token: str | None = os.getenv("TELEGRAM_BOT_TOKEN") or None
    gemini_api_key: str | None = os.getenv("GEMINI_API_KEY") or None
    database_url: str = os.getenv("DATABASE_URL", "sqlite:///data/family_memory.db")

    photos_dir: Path = PROJECT_ROOT / "data" / "photos"
    sample_data_dir: Path = PROJECT_ROOT / "data" / "sample_data"


settings = Settings()


def check_settings() -> None:
    """Print which settings are present, WITHOUT printing secret values."""
    print(f"Project root : {PROJECT_ROOT}")
    print(f"Photos folder: {settings.photos_dir} (exists: {settings.photos_dir.exists()})")
    print(f"Database URL : {settings.database_url}")
    for name in ("telegram_bot_token", "gemini_api_key"):
        value = getattr(settings, name)
        status = "set" if value else "MISSING"
        print(f"{name:<19}: {status}")


if __name__ == "__main__":
    check_settings()