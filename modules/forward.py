import logging
import asyncio
import pytz
from datetime import datetime
from pyrogram import Client, filters
from pyrogram.errors import FloodWait
from .regix import copy_msg, delete_data, FloodWaitTime
from config import OWNER_ID
from database.utils import get_search_results, Media
from database import get_chat

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

IST = pytz.timezone("Asia/Kolkata")
MessageCount = 0
is_running = False

@Client.on_message(filters.command("forward"))
async def forward(bot, message):
    global is_running, MessageCount, FloodWaitTime

    if message.from_user.id not in OWNER_ID:
        return await message.reply_text("Who the hell are you!!")

    if is_running:
        return await message.reply_text("A task is already running.")

    chat_id = await get_chat()
    if not chat_id:
        return await message.reply_text("First set target chat where you want to forward files!")

    is_running = True
    m = await message.reply_text("Forwarding Started!")

    try:
        while await Media.count_documents() != 0:
            data = await get_search_results()
            if not data:
                break

            for msg in data:
                try:
                    await copy_msg(msg, bot, message, chat_id)
                    await delete_data(msg)
                    MessageCount += 1

                    datetime_ist = datetime.now(IST).strftime("%I:%M:%S %p - %d %B %Y")
                    await m.edit_text(
                        f"Total Forwarded: <code>{MessageCount}</code>\n"
                        f"Sleeping for {FloodWaitTime} Second\n"
                        f"Last Forwarded at {datetime_ist}"
                    )
                    
                except Exception as e:
                    logger.exception(e)
                    continue

        await m.edit_text(f"✅ Successfully Forwarded {MessageCount} messages")

    except Exception as e:
        logger.exception(e)
        await message.reply_text(f"Error: {e}")

    finally:
        is_running = False
        MessageCount = 0
