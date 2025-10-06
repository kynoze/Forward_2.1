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
progress_data = {}  # Stores per-user forwarding status


def build_kb(user_id):
    """Return static buttons: Cancel + Progress"""
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("❌ Cancel", callback_data=f"cancel_forward_{user_id}"),
            InlineKeyboardButton("📊 Progress", callback_data=f"progress_alert_{user_id}")
        ]
    ])


async def safe_edit_text(m, text, last_text=None):
    """Edit only if content changed, ignore edit errors."""
    try:
        if last_text is not None and text == last_text:
            return
        await m.edit_text(text, reply_markup=build_kb(m.chat.id))
    except (MessageNotModified, RPCError, FloodWait):
        pass


@app.on_message(filters.command("forward"))
async def forward(bot, message):
    user_id = message.from_user.id
    if user_id not in OWNER_ID:
        return await message.reply_text("You are not allowed!")

    if forward_lock.locked():
        return await message.reply_text("A task is already running.")

    async with forward_lock:
        chat_id = await get_chat()
        if not chat_id:
            return await message.reply_text("First set target chat!")

        # Initialize status
        errors = 0
        message_count = 0
        cancel_forwarding[user_id] = False
        progress_data[user_id] = {"forwarded": 0, "errors": 0, "sleeping": None}

        m = await message.reply_text(
            "Forwarding Started!",
            reply_markup=build_kb(user_id)
        )

        last_progress_text = ""
        update_interval = 5
        last_update_time = 0

        try:
            while True:
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

                    # Forward message and handle FloodWait
                    success, floodwait_seconds = await copy_msg(msg, bot, chat_id)
                    if floodwait_seconds:
                        progress_data[user_id]["sleeping"] = floodwait_seconds
                        logger.info(f"FloodWait: Sleeping for {floodwait_seconds}s")
                        slept = 0
                        interval = 1
                        while slept < floodwait_seconds:
                            if cancel_forwarding.get(user_id):
                                break
                            await asyncio.sleep(min(interval, floodwait_seconds - slept))
                            slept += interval
                        progress_data[user_id]["sleeping"] = None

                    if not success:
                        errors += 1
                        progress_data[user_id]["errors"] = errors
                        continue

                    deleted = await delete_data(msg)
                    if not deleted:
                        errors += 1
                        progress_data[user_id]["errors"] = errors
                        break

                    message_count += 1
                    progress_data[user_id]["forwarded"] = message_count

                    # Update progress occasionally
                    now = asyncio.get_event_loop().time()
                    if (now - last_update_time) > update_interval:
                        dt_str = datetime.now(IST).strftime("%I:%M:%S %p - %d %B %Y")
                        progress_text = f"✅ Forwarded: {message_count}\n❌ Errors: {errors}\nLast: {dt_str}"
                        await safe_edit_text(m, progress_text, last_progress_text)
                        last_progress_text = progress_text
                        last_update_time = now

                    await asyncio.sleep(1)

            if not cancel_forwarding.get(user_id):
                dt_str = datetime.now(IST).strftime("%I:%M:%S %p - %d %B %Y")
                final_text = f"✅ Forwarded: {message_count}\n❌ Errors: {errors}\nLast: {dt_str}"
                await safe_edit_text(m, final_text)

        finally:
            cancel_forwarding[user_id] = False
            progress_data.pop(user_id, None)


@app.on_callback_query(filters.regex(r"^cancel_forward_(\d+)$"))
async def cancel_forwarding_callback(client, callback_query):
    user_id = int(callback_query.matches[0].group(1))
    if callback_query.from_user.id != user_id or user_id not in OWNER_ID:
        await callback_query.answer("Not allowed.", show_alert=True)
        return
    cancel_forwarding[user_id] = True
    await callback_query.answer("Cancelling...", show_alert=True)


@app.on_callback_query(filters.regex(r"^progress_alert_(\d+)$"))
async def show_progress_alert(client, callback_query):
    user_id = int(callback_query.matches[0].group(1))
    data = progress_data.get(user_id)
    if not data:
        await callback_query.answer("No progress yet.", show_alert=True)
        return

    text = f"✅ Forwarded: {data['forwarded']}\n❌ Errors: {data['errors']}"
    if data.get("sleeping"):
        text += f"\n⏳ Sleeping for {data['sleeping']}s due to FloodWait"

    await callback_query.answer(text, show_alert=True)
