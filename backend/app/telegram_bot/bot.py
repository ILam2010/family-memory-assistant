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


@require_member
async def echo(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    text = update.message.text
    logger.info("Message from id=%s (length %d)", update.effective_user.id, len(text))
    await update.message.reply_text(f"You said: {text}")


# ---- Admins only -------------------------------------------------------------

@require_admin
async def admin_check_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text("You are an ADMIN. This command is admin-only.")


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
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, echo))
    return application


def main() -> None:
    application = build_application()
    logger.info(
        "Bot starting. Approved admins: %d, members: %d",
        len(settings.admin_ids),
        len(settings.member_ids),
    )
    application.run_polling()


if __name__ == "__main__":
    main()