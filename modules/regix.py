import logging
from pyrogram.errors import FloodWait
from database.utils import Media

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


async def copy_msg(msg, bot, chat_id):
    """
    Forward a message using cached media.
    Returns (success: bool, flood_seconds: Optional[int])
    """
    try:
        await bot.send_cached_media(
            chat_id=int(chat_id),
            file_id=msg.file_id,
            caption=getattr(msg, "caption", "")
        )
        return True, None
    except FloodWait as e:
        logger.warning(f"FloodWait encountered: {e.value} seconds")
        return False, e.value
    except Exception:
        logger.exception("Failed to copy message")
        return False, None


async def delete_data(data):
    """
    Delete a Media document by file_id (_id in DB).
    """
    result = await Media.collection.delete_one({
        '_id': data.file_id
    })
    if result.deleted_count:
        logger.info(f"[DB] Deleted {data.file_id}")
        return True
    logger.info(f"[DB] Not found: {data.file_id}")
    return False
