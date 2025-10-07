import logging
import asyncio
import pytz
from datetime import datetime
from pyrogram import filters
from pyrogram.errors import FloodWait, RPCError
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from .regix import copy_msg, delete_data
from config import OWNER_ID
from database.utils import get_search_results
from database import get_chat
from bot import app

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

IST = pytz.timezone("Asia/Kolkata")
forward_lock = asyncio.Lock()
cancel_forwarding = {}
progress_status = {}


# 🔘 Build inline keyboard for control buttons
def build_control_kb(user_id):
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("📊 Status", callback_data=f"check_progress_{user_id}"),
            InlineKeyboardButton("❌ Cancel", callback_data=f"cancel_forward_{user_id}")
        ]
    ])


@app.on_message(filters.command("forward"))
async def forward(bot, message):
    user_id = message.from_user.id
    if user_id not in OWNER_ID:
        return await message.reply_text("Who the hell are you!!")

    if forward_lock.locked():
        return await message.reply_text("⚠️ A forwarding task is already running.")

    async with forward_lock:
        chat_id = await get_chat()
        if not chat_id:
            return await message.reply_text("❗ First set target chat where you want to forward files!")

        cancel_forwarding[user_id] = False
        progress_status[user_id] = {"forwarded": 0, "errors": 0, "last_time": None}

        # Start message with control buttons
        m = await message.reply_text(
            "🚀 Forwarding Started...",
            reply_markup=build_control_kb(user_id)
        )

        try:
            while True:
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

                    floodwait_attempts = 0
                    max_floodwait_attempts = 5

                    while floodwait_attempts < max_floodwait_attempts:
                        try:
                            success, floodwait_seconds = await copy_msg(msg, bot, chat_id)

                            # If success is False and floodwait_seconds > 0, sleep for that duration
                            if not success and floodwait_seconds:
                                slept = 0
                                interval = 1
                                while slept < floodwait_seconds:
                                    if cancel_forwarding.get(user_id):
                                        await m.edit_text("❌ Forwarding cancelled by user.")
                                        break
                                    await asyncio.sleep(min(interval, floodwait_seconds - slept))
                                    slept += interval
                                floodwait_attempts += 1
                                continue

                        except FloodWait as e:
                            logger.warning(f"FloodWait for {e.value} seconds.")
                            await asyncio.sleep(e.value)
                            floodwait_attempts += 1
                            continue

                        except RPCError as e:
                            logger.error(f"RPCError: {e}")
                            progress_status[user_id]["errors"] += 1
                            break

                        except Exception as e:
                            logger.exception(e)
                            progress_status[user_id]["errors"] += 1
                            break

                        # Break out of retry loop if success
                        break

                    else:
                        # Exceeded max floodwait attempts
                        logger.error(f"FloodWait loop exceeded for message: {msg}")
                        progress_status[user_id]["errors"] += 1
                        continue

                    if not success:
                        progress_status[user_id]["errors"] += 1
                        continue

                    deleted = await delete_data(msg)
                    if not deleted:
                        progress_status[user_id]["errors"] += 1
                        continue

                    progress_status[user_id]["forwarded"] += 1
                    progress_status[user_id]["last_time"] = datetime.now(IST).strftime("%I:%M:%S %p - %d %B %Y")

                    await asyncio.sleep(1)

            if not cancel_forwarding.get(user_id):
                await m.edit_text(
                    f"✅ Forwarding Completed!\n"
                    f"Total Forwarded: <code>{progress_status[user_id]['forwarded']}</code>\n"
                    f"Errors: <code>{progress_status[user_id]['errors']}</code>\n"
                    f"Last at: {progress_status[user_id]['last_time']}"
                )

        except Exception as e:
            logger.exception(e)
            await message.reply_text(f"❌ Error: {e}")

        finally:
            cancel_forwarding[user_id] = False
            progress_status.pop(user_id, None)


# ❌ Cancel button
@app.on_callback_query(filters.regex(r"^cancel_forward_(\d+)$"))
async def cancel_forwarding_callback(client, callback_query):
    user_id = int(callback_query.matches[0].group(1))
    if callback_query.from_user.id != user_id or user_id not in OWNER_ID:
        return await callback_query.answer("Not allowed!", show_alert=True)

    cancel_forwarding[user_id] = True
    await callback_query.answer("🛑 Cancelling forwarding...", show_alert=True)


# 📊 Status button
@app.on_callback_query(filters.regex(r"^check_progress_(\d+)$"))
async def check_progress_callback(client, callback_query):
    user_id = int(callback_query.matches[0].group(1))
    if callback_query.from_user.id != user_id or user_id not in OWNER_ID:
        return await callback_query.answer("Not allowed!", show_alert=True)

    status = progress_status.get(user_id)
    if not status:
        return await callback_query.answer("No active forwarding task.", show_alert=True)

    text = (
        f"📊 Forwarding Progress:\n\n"
        f"✅ Forwarded: {status['forwarded']}\n"
        f"⚠️ Errors: {status['errors']}\n"
        f"🕓 Last at: {status['last_time'] or 'N/A'}"
    )
    await callback_query.answer(text, show_alert=True)
