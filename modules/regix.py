import asyncio
import logging
from pyrogram.errors import FloodWait
from database.utils import Media

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

async def copy_msg(msg, bot, message, chat_id, m, message_count):
    max_attempts = 5
    attempt = 0
    while attempt < max_attempts:
        try:
            await bot.send_cached_media(
                chat_id=int(chat_id),
                file_id=msg.file_id,
                caption=msg.caption
            )
            return True
        except FloodWait as e:
            await m.edit_text(
                f"Total Forwarded: <code>{message_count}</code>\n"
                f"Sleeping for <code>{e.value}</code> seconds"
            )
            await asyncio.sleep(e.value)
            attempt += 1
        except Exception as e:
            logger.exception("Failed to copy message")
            return False
    logger.error("Max attempts reached for FloodWait in copy_msg")
    return False

async def delete_data(data):
    try:
        result = await Media.collection.delete_one({
            'file_id': data.file_id,
            'use': 'forward'
        })
        if result.deleted_count:
            logger.info(f"[DB] Deleted {data.file_id}")
            return True
        logger.warning(f"[DB] Not found: {data.file_id}")
        return False
    except Exception as e:
        logger.exception(f"DB error deleting {data.file_id}")
        return False
