import logging
import asyncio
import pytz
from datetime import datetime
from pyrogram import filters
from pyrogram.errors import FloodWait, MessageNotModified, RPCError
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
cancel_forwarding = {}

def build_progress_text(message_count, errors, last_time, sleeping_for=None):
    if sleeping_for:
        return (
            f"Total Forwarded: <code>{message_count}</code>\n"
            f"Total Error: <code>{errors}</code>\n"
            f"Sleeping for <code>{sleeping_for}</code> seconds"
        )
    else:
        return (
            f"Total Forwarded: <code>{message_count}</code>\n"
            f"Total Error: <code>{errors}</code>\n"
            f"Last Forwarded at {last_time}"
        )

def build_cancel_kb(user_id):
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("❌ Cancel", callback_data=f"cancel_forward_{user_id}")]
    ])

async def safe_edit_text(m, text, kb=None, last_text=None):
    """Edit only if content changed and handle Telegram limits/errors gracefully."""
    try:
        if last_text is not None and text == last_text:
            return  # Avoid unnecessary edits
        await m.edit_text(text, reply_markup=kb)
    except MessageNotModified:
        pass  # Telegram: message is not modified
    except FloodWait as e:
        logger.warning(f"FloodWait while editing progress message: {e.value}")
        await asyncio.sleep(e.value)
    except RPCError as e:
        logger.error(f"RPCError while editing progress message: {e}")

@app.on_message(filters.command("forward"))
async def forward(bot, message):
    user_id = message.from_user.id
    if user_id not in OWNER_ID:
        return await message.reply_text("Who the hell are you!!")

    if forward_lock.locked():
        return await message.reply_text("A task is already running.")

    async with forward_lock:
        chat_id = await get_chat()
        if not chat_id:
            return await message.reply_text("First set target chat where you want to forward files!")

        errors = 0
        message_count = 0
        cancel_forwarding[user_id] = False

        m = await message.reply_text(
            "Forwarding Started!",
            reply_markup=build_cancel_kb(user_id)
        )

        last_progress_text = ""
        last_update_time = 0
        update_interval = 5  # seconds between forced progress updates

        try:
            while await Media.count_documents() != 0:
                if cancel_forwarding.get(user_id):
                    await safe_edit_text(m, "❌ Forwarding cancelled by user.")
                    break

                data = await get_search_results()
                if not data:
                    break

                for msg in data:
                    if cancel_forwarding.get(user_id):
                        await safe_edit_text(m, "❌ Forwarding cancelled by user.")
                        break

                    # Limit FloodWait retries to 5
                    floodwait_attempts = 0
                    max_floodwait_attempts = 5
                    while floodwait_attempts < max_floodwait_attempts:
                        success, floodwait_seconds = await copy_msg(msg, bot, message, chat_id)
                        if floodwait_seconds:
                            progress_text = build_progress_text(
                                message_count, errors,
                                datetime.now(IST).strftime("%I:%M:%S %p - %d %B %Y"),
                                sleeping_for=floodwait_seconds
                            )
                            await safe_edit_text(m, progress_text, build_cancel_kb(user_id), last_progress_text)
                            last_progress_text = progress_text
                            await asyncio.sleep(floodwait_seconds)
                            floodwait_attempts += 1
                            continue
                        break
                    else:
                        # Exceeded max floodwait attempts
                        logger.error(f"FloodWait loop exceeded for message: {msg}")
                        errors += 1
                        continue

                    if not success:
                        logger.error(f"Failed to copy message: {msg}")
                        errors += 1
                        continue

                    deleted = await delete_data(msg)
                    if not deleted:
                        logger.error(f"Failed to delete message data for msg: {msg}")
                        errors += 1
                        break  # Break the message loop if deletion fails

                    message_count += 1

                    # Only update if message text changes, or enough time has passed
                    datetime_ist = datetime.now(IST).strftime("%I:%M:%S %p - %d %B %Y")
                    progress_text = build_progress_text(message_count, errors, datetime_ist)
                    now = asyncio.get_event_loop().time()
                    if progress_text != last_progress_text or (now - last_update_time) > update_interval:
                        await safe_edit_text(m, progress_text, build_cancel_kb(user_id), last_progress_text)
                        last_progress_text = progress_text
                        last_update_time = now

                    await asyncio.sleep(1)

            if not cancel_forwarding.get(user_id):
                datetime_ist = datetime.now(IST).strftime("%I:%M:%S %p - %d %B %Y")
                final_text = (
                    f"✅ Successfully Forwarded <code>{message_count}</code> messages\n"
                    f"Total Error: <code>{errors}</code>\n"
                    f"Last Forwarded at {datetime_ist}"
                )
                await safe_edit_text(m, final_text)

        except Exception as e:
            logger.exception(e)
            await message.reply_text(f"Error: {e}")

        finally:
            cancel_forwarding[user_id] = False

@app.on_callback_query(filters.regex(r"^cancel_forward_(\d+)$"))
async def cancel_forwarding_callback(client, callback_query):
    user_id = int(callback_query.matches[0].group(1))
    if callback_query.from_user.id not in OWNER_ID or callback_query.from_user.id != user_id:
        await callback_query.answer("You are not allowed to cancel this task.", show_alert=True)
        return
    cancel_forwarding[user_id] = True
    await callback_query.answer("Cancelling forwarding...", show_alert=True)
