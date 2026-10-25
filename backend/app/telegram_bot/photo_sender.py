"""Turn photo IDs into pictures sent through Telegram."""

import logging

from telegram import InputMediaPhoto, Message
from telegram.error import TelegramError

from app.database.session import SessionLocal
from app.services import photo_service, photo_storage

logger = logging.getLogger(__name__)

MAX_PHOTOS_PER_REPLY = 5


def _load_items(photo_ids: list[int]) -> list[tuple[int, bytes, str]]:
    """Read each photo's file and build a caption. Skips any that can't be loaded."""
    items: list[tuple[int, bytes, str]] = []
    with SessionLocal() as session:
        for photo_id in photo_ids[:MAX_PHOTOS_PER_REPLY]:
            photo = photo_service.get_photo(session, photo_id)
            if photo is None:
                continue
            try:
                data = photo_storage.resolve_photo_path(photo.file_path).read_bytes()
            except (OSError, ValueError):
                logger.warning("File missing for photo #%s", photo_id)
                continue
            caption = f"#{photo.id}\n{photo_service.photo_summary(photo)}".strip()
            items.append((photo_id, data, caption[:1000]))
    return items


async def send_photos(message: Message, photo_ids: list[int]) -> int:
    """Send photos as one picture or an album. Returns how many were sent."""
    items = _load_items(photo_ids)
    if not items:
        return 0
    try:
        if len(items) == 1:
            _, data, caption = items[0]
            await message.reply_photo(photo=data, caption=caption)
        else:
            media = [InputMediaPhoto(media=data, caption=caption) for _, data, caption in items]
            await message.reply_media_group(media=media)
    except TelegramError:
        logger.exception("Sending photos failed")
        return 0
    return len(items)