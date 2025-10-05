import logging
import asyncio
import pytz
from datetime import datetime
from pyrogram import Client, filters
from pyrogram.errors import FloodWait
from .regix import copy_msg, delete_data
from config import OWNER_ID
from database.utils import get_search_results, Media
from database import get_chat
from bot import app

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

IST = pytz.timezone("Asia/Kolkata")

# Global variables
MessageCount = 0
is_running = False

@app.on_message(filters.command("forward"))
async def forward(bot, message):
    """
    Forward messages from DB to target chat one by one.
    Handles FloodWait automatically and updates progress message.
    """
    global is_running, MessageCount

    if message.from_user.id not in OWNER_ID:
        return await message.reply_text("Who the hell are you!!")

    if is_running:
        return await message.reply_text("A task is already running.")

    chat_id = await get_chat()
    if not chat_id:
        return await message.reply_text("First set target chat where you want to forward files!")

    is_running = True
    errors = 0

    m = await message.reply_text("Forwarding Started!")

    try:
        while await Media.count_documents() != 0:
            data = await get_search_results()
            if not data:
                is_running = False
                break

            for msg in data:
                try:
                    
                    await copy_msg(msg, bot, message, chat_id, m, MessageCount)
                    delete = await delete_data(msg)
                    if not delete:
                        is_running = False
                        break

                    MessageCount += 1

                    if MessageCount % 10 == 0:
                        datetime_ist = datetime.now(IST).strftime("%I:%M:%S %p - %d %B %Y")
                        await m.edit_text(
                            f"Total Forwarded: <code>{MessageCount}</code>\n"
                            f"Total Error: <code>{errors}</code>\n"
                            f"Last Forwarded at {datetime_ist}"
                        )

                except Exception as e:
                    logger.exception(e)
                    errors += 1
                    continue    
                    
        datetime_ist = datetime.now(IST).strftime("%I:%M:%S %p - %d %B %Y")
        await m.edit_text(
            f"✅ Successfully Forwarded <code>{MessageCount}</code> messages\n"
            f"Last Forwarded at {datetime_ist}"
        )

    except Exception as e:
        logger.exception(e)
        is_running = False
        await message.reply_text(f"Error: {e}")

    finally:
        is_running = False
        MessageCount = 0
