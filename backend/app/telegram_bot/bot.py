"""Telegram bot entry point (Phase 3: authorization).

Run from the backend/ folder:
    python -m app.telegram_bot.bot
"""

import logging

from telegram import Update
from telegram.ext import (
    Application,
    ApplicationBuilder,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

from app.config import settings
from app.services.auth_service import get_member
from app.telegram_bot.auth import DENIED_TEXT, require_admin, require_member

from app.database.models import Role
from app.database.session import SessionLocal, init_db
from app.services import member_service

from telegram.error import TelegramError

from app.services import photo_service, photo_storage

logging.basicConfig(
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    level=logging.INFO,
)
# The HTTP library logs request URLs, which contain the bot token. Keep it quiet.
logging.getLogger("httpx").setLevel(logging.WARNING)
logger = logging.getLogger(__name__)

WELCOME_TEXT = (
    "Welcome to Family Memory Assistant.\n\n"
    "Soon you'll be able to ask things like:\n"
    '"Show me photos from Christmas 2023"\n'
    '"Tell me about our Hawassa trip"\n'
    '"Find pictures with Grandma"'
)


# ---- Open to everyone (they must be able to get their ID) -------------------

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    member = get_member(user.id)
    if member is None:
        logger.warning("/start from unapproved user id=%s", user.id)
        await update.message.reply_text(DENIED_TEXT)
        return
    logger.info("/start from %s id=%s", member.role.value, user.id)
    await update.message.reply_text(f"{WELCOME_TEXT}\n\nYour role: {member.role.value}")


async def whoami_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Tell anyone their own Telegram ID so they can ask the admin for access."""
    user = update.effective_user
    await update.message.reply_text(
        f"Your Telegram ID is: {user.id}\n"
        "Send this number to the family admin to request access."
    )


# ---- Family members only -----------------------------------------------------

@require_member
async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        "Just send me a message. Later you'll be able to search and upload memories."
    )


MAX_DESCRIPTION_LENGTH = 2000


@require_member
async def photo_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Runs when a family member sends a photo."""
    message = update.message
    member = context.user_data["member"]

    largest = message.photo[-1]  # the list goes small -> large
    relative_path, absolute_path = photo_storage.new_photo_location()

    try:
        telegram_file = await largest.get_file()
        await telegram_file.download_to_drive(custom_path=absolute_path)
    except TelegramError:
        logger.exception("Photo download failed for user id=%s", update.effective_user.id)
        await message.reply_text("Sorry, I couldn't download that photo. Please try again.")
        return

    caption = (message.caption or "").strip()[:MAX_DESCRIPTION_LENGTH] or None

    with SessionLocal() as session:
        photo = photo_service.create_photo(
            session,
            uploader_id=member.member_id,
            file_path=relative_path,
            telegram_file_id=largest.file_id,
            description=caption,
        )
        photo_id = photo.id

    logger.info("Photo #%s saved for user id=%s", photo_id, update.effective_user.id)

    if caption:
        context.user_data.pop("awaiting_description_for", None)
        await message.reply_text(f"Saved photo #{photo_id} with your description.")
    else:
        context.user_data["awaiting_description_for"] = photo_id
        await message.reply_text(
            f"Saved photo #{photo_id}. Send me a description now "
            "(for example: \"Our trip to Hawassa in 2024 with Grandma\"), "
            "or send /skip."
        )


@require_member
async def text_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Runs for normal text messages."""
    member = context.user_data["member"]
    photo_id = context.user_data.get("awaiting_description_for")

    if photo_id is None:
        await update.message.reply_text(
            "Send me a photo to save a memory. Searching memories is coming soon."
        )
        return

    description = update.message.text.strip()[:MAX_DESCRIPTION_LENGTH]
    with SessionLocal() as session:
        updated = photo_service.set_description(
            session, photo_id, member.member_id, description
        )
    context.user_data.pop("awaiting_description_for", None)

    if updated:
        await update.message.reply_text(f"Description saved for photo #{photo_id}.")
    else:
        await update.message.reply_text("Sorry, I couldn't attach that description.")


@require_member
async def skip_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    context.user_data.pop("awaiting_description_for", None)
    await update.message.reply_text("OK, no description for that photo.")


@require_member
async def my_photos_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    member = context.user_data["member"]
    with SessionLocal() as session:
        photos = photo_service.list_by_uploader(session, member.member_id)
    if not photos:
        await update.message.reply_text("You haven't uploaded any photos yet.")
        return
    lines = [
        f"#{p.id}: {(p.description or '(no description)')[:60]}" for p in photos[-20:]
    ]
    await update.message.reply_text(
        f"You have {len(photos)} photo(s). Latest:\n" + "\n".join(lines)
    )


@require_member
async def photo_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """/photo <id> : send a stored photo back (family members can view all photos)."""
    if not context.args or not context.args[0].isdigit():
        await update.message.reply_text("Usage: /photo <number>\nExample: /photo 1")
        return

    with SessionLocal() as session:
        photo = photo_service.get_photo(session, int(context.args[0]))
        if photo is None:
            await update.message.reply_text("I couldn't find a photo with that number.")
            return
        file_path, description = photo.file_path, photo.description

    try:
        path = photo_storage.resolve_photo_path(file_path)
        with open(path, "rb") as image:
            await update.message.reply_photo(
                photo=image, caption=(description or "")[:1000] or None
            )
    except (OSError, ValueError):
        logger.exception("Could not send photo file %s", file_path)
        await update.message.reply_text("Sorry, I couldn't load that photo file.")


# ---- Admins only -------------------------------------------------------------

@require_admin
async def admin_check_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text("You are an ADMIN. This command is admin-only.")


@require_admin
async def add_member_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Admin only: /add_member <telegram_id> <name>"""
    if len(context.args) < 2 or not context.args[0].isdigit():
        await update.message.reply_text(
            "Usage: /add_member <telegram_id> <name>\n"
            "Example: /add_member 123456789 Mimi"
        )
        return
    telegram_id = int(context.args[0])
    name = " ".join(context.args[1:])[:100]
    with SessionLocal() as session:
        try:
            member_service.create_member(session, telegram_id, name=name)
        except ValueError:
            await update.message.reply_text("That Telegram ID is already registered.")
            return
    await update.message.reply_text(f"Added {name} as a family MEMBER.")


@require_admin
async def members_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Admin only: list family members."""
    with SessionLocal() as session:
        members = member_service.list_members(session)
    lines = [
        f"{m.id}. {m.name or '(no name)'} - {m.role.value} ({m.status.value})"
        for m in members
    ]
    await update.message.reply_text("Family members:\n" + "\n".join(lines))


def build_application() -> Application:
    if not settings.telegram_bot_token:
        raise RuntimeError("TELEGRAM_BOT_TOKEN is missing. Check your .env file.")

    application = (
        ApplicationBuilder()
        .token(settings.telegram_bot_token)
        .connect_timeout(30)
        .read_timeout(30)
        .write_timeout(30)
        .pool_timeout(30)
        .get_updates_connect_timeout(30)
        .get_updates_read_timeout(30)
        .get_updates_write_timeout(30)
        .get_updates_pool_timeout(30)
        .build()
    )

    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("whoami", whoami_command))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("admin_check", admin_check_command))
    application.add_handler(CommandHandler("add_member", add_member_command))
    application.add_handler(CommandHandler("members", members_command))
    application.add_handler(CommandHandler("skip", skip_command))
    application.add_handler(CommandHandler("my_photos", my_photos_command))
    application.add_handler(CommandHandler("photo", photo_command))
    application.add_handler(MessageHandler(filters.PHOTO, photo_handler))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, text_handler))
    return application


def main() -> None:
    init_db()
    with SessionLocal() as session:
        member_service.seed_from_env(session)
        total = len(member_service.list_members(session))
    application = build_application()
    logger.info("Bot starting. Members in database: %d", total)
    application.run_polling()


if __name__ == "__main__":
    main()