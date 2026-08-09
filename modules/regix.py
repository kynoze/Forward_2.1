import logging

from pyrogram.enums import ParseMode
from pyrogram.errors import FloodWait

from database.utils import Media
from helper.clean_file_name import clean_file_name
from .other_cmd import CLEAN_FILE_NAME, CUSTOM_CAPTION_TEXT

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


async def copy_msg(msg, bot, chat_id, user_id):
    """Forward a message using cached media.

    Returns (success: bool, flood_seconds: Optional[int])
    """
    # Original caption
    caption = msg.caption or ""

    # Clean file name/caption if enabled
    if CLEAN_FILE_NAME.get(user_id, False):
        caption = clean_file_name(caption)

    # Get user's custom caption
    add_caption = CUSTOM_CAPTION_TEXT.get(user_id, "")

    # Combine captions and make final caption bold
    if add_caption:
        if caption:
            caption = f"**{caption}\n\n{add_caption}**"
        else:
            caption = f"**{add_caption}**"
    elif caption:
        caption = f"**{caption}**"

    try:
        await bot.send_cached_media(
            chat_id=int(chat_id),
            file_id=msg.file_id,
            caption=caption,
            parse_mode=ParseMode.MARKDOWN,
        )

        return True, None

    except FloodWait as e:
        logger.warning(f"FloodWait encountered: {e.value} seconds")
        return False, e.value

    except Exception:
        logger.exception("Failed to copy message")
        return False, None


async def delete_data(data):
    """Delete a Media document by file_id (_id in DB)."""
    result = await Media.collection.delete_one({"use": "forward"})

    if result.deleted_count:
        logger.info(f"[DB] Deleted {data.caption}")
        return True

    logger.info(f"[DB] Not found: {data.caption}")
    return False
  
