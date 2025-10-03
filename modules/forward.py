# plugins/forward.py
import logging
import asyncio
import pytz
from datetime import datetime

from pyrogram import Client, filters
from pyrogram.errors import FloodWait

from config import OWNER_ID, TO_CHANNEL
from database.utils import get_search_results, Data  # Data is uMongo Document class

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

IST = pytz.timezone("Asia/Kolkata")
MessageCount = 0
status = set()          # simple set to avoid overlapping runs

def is_owner(user_id: int) -> bool:
    if isinstance(OWNER, (list, tuple, set)):
        return user_id in OWNER
    return user_id == OWNER

@Client.on_message(filters.command("forward"))
async def forward(bot, message):
    global MessageCount
    if 1 in status:
        await message.reply_text("A task is already running.")
        return

    m = await bot.send_message(chat_id=message.from_user.id, text="Started Forwarding")

    while await Data.count_documents() != 0:
        data = await get_search_results()
        for msg in data:
            to_chat=Config.TO_CHANNEL 
            file_id=msg.id
            caption=msg.caption
            file_type=msg.file_type

            try:
                if file_type == "media":
                    try:
                        await bot.send_cached_media(
                            chat_id=to_chat,
                            file_id=file_id,
                            caption=caption
                        )
                    except FloodWait as e:
                        await asyncio.sleep(e.value)
                        await bot.copy_message(
                            chat_id=to_chat,
                            file_id=file_id,
                            caption=caption
                        )               
                    await asyncio.sleep(1)
                if file_type == "messages":
                    try:
                        await bot.copy_message(
                            chat_id=to_chat,
                            from_chat_id=channel_id,
                            parse_mode=enums.ParseMode.MARKDOWN,       
                            caption=caption,
                            message_id=message_id
                        )
                    except FloodWait as e:
                        await asyncio.sleep(e.value)
                        await bot.copy_message(
                            chat_id=to_chat,
                            from_chat_id=channel_id,
                            parse_mode=enums.ParseMode.MARKDOWN,       
                            caption=caption,
                            message_id=message_id
                        )
                try:
                    status.add(1)
                except:
                    pass
            except Exception as e:
                logger.exception(e)
                pass

            await Data.collection.delete_one({
                'use': 'forward',
                'file_type': file_type,
                'channel_id': channel_id,
                'message_id': message_id
                })

            MessageCount += 1
            
            try:
                datetime_ist = datetime.now(IST)
                ISTIME = datetime_ist.strftime("%I:%M:%S %p - %d %B %Y")
                await m.edit(text=f"Total Forwarded: <code>{MessageCount}</code>\nForwarded Using: Bot\nSleeping for {1} Seconds\nLast Forwarded at {ISTIME}")
            except Exception as e:
                logger.exception(e)
                await bot.send_message(chat_id=OWNER, text=f"LOG-Error: {e}")
                pass

    logger.info("Finished")

    try:
        await m.edit(text=f'Successfully Forwarded {MessageCount} messages')
    except Exception as e:
        await bot.send_message(OWNER, e)
        logger.exception(e)
        pass

    try:
        status.remove(1)
    except:
        pass

    MessageCount = 0
