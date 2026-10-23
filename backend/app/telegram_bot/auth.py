"""Decorators that guard Telegram handlers."""

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


def require_member(handler):
    """Only run the handler if the sender is an approved family member."""

    @wraps(handler)
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE):
        user = update.effective_user
        message = update.effective_message
        if user is None or message is None:
            return  # e.g. channel posts: nobody to answer

        member = get_member(user.id)
        if member is None:
            logger.warning("Access denied for user id=%s", user.id)
            await message.reply_text(DENIED_TEXT)
            return

        context.user_data["member"] = member
        return await handler(update, context)

    return wrapper


def require_admin(handler):
    """Only run the handler if the sender is an approved ADMIN."""

    @wraps(handler)
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE):
        user = update.effective_user
        message = update.effective_message
        if user is None or message is None:
            return

        member = get_member(user.id)
        if member is None:
            logger.warning("Access denied for user id=%s", user.id)
            await message.reply_text(DENIED_TEXT)
            return
        if not is_admin(member):
            logger.warning("Admin-only command refused for user id=%s", user.id)
            await message.reply_text("Sorry, that command is for family admins only.")
            return

        context.user_data["member"] = member
        return await handler(update, context)

    return wrapper