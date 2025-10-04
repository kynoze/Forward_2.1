import asyncio
from pyrogram.errors import FloodWait
from database.utils import Data  # ✅ Make sure this path is correct for your project


async def copy_msg(msg, bot, message, chat_id):
    """
    Copy a cached message (photo/video/document/etc.) to the target chat.
    Retries automatically if FloodWait occurs.
    """
    try:
        await bot.send_cached_media(
            chat_id=int(chat_id),
            file_id=msg.file_id,
            caption=msg.caption
        )
    except FloodWait as e:
        print(f"[FloodWait] Sleeping for {e.value} seconds...")
        await asyncio.sleep(e.value)
        await copy_msg(msg, bot, message, chat_id)  # Retry automatically
    except Exception as e:
        print(f"[Error] copy_msg: {e}")


async def delete_data(data):
    """
    Delete one specific media record from the MongoDB collection.
    """
    try:
        result = await Data.collection.delete_one({
            'use': data.use,
            'file_id': data.file_id,
            'caption': data.caption
        })
        if result.deleted_count > 0:
            print(f"[DB] Deleted {data.file_id}")
        else:
            print(f"[DB] No record found for {data.file_id}")
    except Exception as e:
        print(f"[Error] delete_data: {e}")
