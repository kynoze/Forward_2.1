import logging
from pyrogram.errors import FloodWait
from database.utils import Media

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

async def copy_msg(msg, bot, message, chat_id):
    try:
        await bot.send_cached_media(
            chat_id=int(chat_id),
            file_id=msg.file_id,
            caption=msg.caption
        )
        return True, None
    except FloodWait as e:
        logger.warning(f"FloodWait encountered: {e.value} seconds")
        return False, e.value
    except Exception as e:
        logger.exception("Failed to copy message")
        return False, None

async def delete_data(data):
    try:
        result = await Media.collection.delete_one({
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
