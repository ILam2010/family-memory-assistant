"""Decorators that guard Telegram handlers.
"""

import logging
from functools import wraps

from telegram import Update
from telegram.ext import ContextTypes

from app.services.auth_service import get_member, is_admin

logger = logging.getLogger(__name__)

DENIED_TEXT = (
    "Sorry, this is a private family assistant and I don't recognise your account.\n\n"
    "Send /whoami to see your Telegram ID, then share it with the family admin "
    "to request access."
)
PRIVATE_ONLY_TEXT = "For privacy, I only work in private chats. Please message me directly."


async def _private_chat_only(update: Update) -> bool:
    user = update.effective_user
    chat = update.effective_chat
    message = update.effective_message
    if user is None or chat is None or message is None:
        return False
    if chat.type != "private":
        logger.warning("Refused non-private chat (type=%s) from user id=%s", chat.type, user.id)
        await message.reply_text(PRIVATE_ONLY_TEXT)
        return False
    return True


async def _authorize(update: Update, context: ContextTypes.DEFAULT_TYPE, need_admin: bool) -> bool:
    if not await _private_chat_only(update):
        return False
    user = update.effective_user
    message = update.effective_message

    member = get_member(user.id)
    if member is None:
        logger.warning("Access denied for user id=%s", user.id)
        await message.reply_text(DENIED_TEXT)
        return False
    if need_admin and not is_admin(member):
        logger.warning("Admin-only command refused for user id=%s", user.id)
        await message.reply_text("Sorry, that command is for family admins only.")
        return False

    context.user_data["member"] = member
    return True


def public_command(handler):
    """For the few commands anyone may use (/start, /whoami). Private chats only."""

    @wraps(handler)
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE):
        if await _private_chat_only(update):
            return await handler(update, context)

    wrapper.auth_level = "public"
    return wrapper


def require_member(handler):
    """Only run the handler for an approved, active family member."""

    @wraps(handler)
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE):
        if await _authorize(update, context, need_admin=False):
            return await handler(update, context)

    wrapper.auth_level = "member"
    return wrapper


def require_admin(handler):
    """Only run the handler for an approved ADMIN."""

    @wraps(handler)
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE):
        if await _authorize(update, context, need_admin=True):
            return await handler(update, context)

    wrapper.auth_level = "admin"
    return wrapper