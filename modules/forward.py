import logging
import asyncio
import pytz
from datetime import datetime
from pyrogram import Client, filters
from pyrogram.errors import FloodWait
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from .regix import copy_msg, delete_data
from config import OWNER_ID
from database.utils import get_search_results, Media
from database import get_chat
from bot import app

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

IST = pytz.timezone("Asia/Kolkata")

forward_lock = asyncio.Lock()
STATS_UPDATE_EVERY = 10  # update status message every 10 forwards

# In-memory cancel flags per user/session
cancel_forwarding = {}

@app.on_message(filters.command("forward"))
async def forward(bot, message):
    """
    Forward messages from DB to target chat one by one.
    Handles FloodWait automatically and updates progress message.
    Allows cancellation via inline button.
    """

    user_id = message.from_user.id
    if user_id not in OWNER_ID:
        return await message.reply_text("Who the hell are you!!")

    # Acquire the lock to prevent concurrent tasks
    if forward_lock.locked():
        return await message.reply_text("A task is already running.")

    async with forward_lock:
        chat_id = await get_chat()
        if not chat_id:
            return await message.reply_text("First set target chat where you want to forward files!")

        errors = 0
        message_count = 0
        stats_count = 0

        cancel_forwarding[user_id] = False  # Reset cancel flag

        m = await message.reply_text(
            "Forwarding Started!",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("❌ Cancel", callback_data=f"cancel_forward_{user_id}")]
            ])
        )

        try:
            while await Media.count_documents() != 0:
                if cancel_forwarding.get(user_id):
                    await m.edit_text("❌ Forwarding cancelled by user.")
                    break

                data = await get_search_results()
                if not data:
                    break

                for msg in data:
                    if cancel_forwarding.get(user_id):
                        await m.edit_text("❌ Forwarding cancelled by user.")
                        break

                    try:
                        success = await copy_msg(msg, bot, message, chat_id, m, message_count)
                        deleted = await delete_data(msg) if success else False

                        if not deleted:
                            logger.error(f"Failed to delete message data for msg: {msg}")
                            errors += 1
                            continue

                        message_count += 1
                        stats_count += 1

                        if stats_count == STATS_UPDATE_EVERY:
                            datetime_ist = datetime.now(IST).strftime("%I:%M:%S %p - %d %B %Y")
                            stats_count = 0
                            await m.edit_text(
                                f"Total Forwarded: <code>{message_count}</code>\n"
                                f"Total Error: <code>{errors}</code>\n"
                                f"Last Forwarded at {datetime_ist}",
                                reply_markup=InlineKeyboardMarkup([
                                    [InlineKeyboardButton("❌ Cancel", callback_data=f"cancel_forward_{user_id}")]
                                ])
                            )

                    except FloodWait as e:
                        logger.warning(f"FloodWait: Sleeping for {e.value} seconds")
                        await asyncio.sleep(e.value)
                        continue
                    except Exception as e:
                        logger.exception(e)
                        errors += 1
                        continue

                    await asyncio.sleep(1)

            if not cancel_forwarding.get(user_id):
                datetime_ist = datetime.now(IST).strftime("%I:%M:%S %p - %d %B %Y")
                await m.edit_text(
                    f"✅ Successfully Forwarded <code>{message_count}</code> messages\n"
                    f"Total Error: <code>{errors}</code>\n"
                    f"Last Forwarded at {datetime_ist}"
                )

        except Exception as e:
            logger.exception(e)
            await message.reply_text(f"Error: {e}")

        finally:
            cancel_forwarding[user_id] = False  # Clean up

# Inline button handler for cancellation
@app.on_callback_query(filters.regex(r"^cancel_forward_(\d+)$"))
async def cancel_forwarding_callback(client, callback_query):
    user_id = int(callback_query.matches[0].group(1))

    # Only allow OWNER_ID to cancel
    if callback_query.from_user.id not in OWNER_ID or callback_query.from_user.id != user_id:
        await callback_query.answer("You are not allowed to cancel this task.", show_alert=True)
        return

    cancel_forwarding[user_id] = True
    await callback_query.answer("Cancelling forwarding...", show_alert=True)
