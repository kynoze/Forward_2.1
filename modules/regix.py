import asyncio
from pyrogram.errors import FloodWait
from database.utils import Media

FloodWaitTime = 0

async def copy_msg(msg, bot, message, chat_id):
    global FloodWaitTime
    while True:
        try:
            FloodWaitTime = 0
            await bot.send_cached_media(
                chat_id=int(chat_id),
                file_id=msg.file_id,
                caption=msg.caption
            )
            break
        except FloodWait as e:
            FloodWaitTime = e.value
            print(f"[FloodWait] Sleeping for {e.value} seconds...")
            await asyncio.sleep(FloodWaitTime)
        except Exception as e:
            print(f"[Error] copy_msg: {e}")
            break

async def delete_data(data):
    """
    Delete one specific media record from the MongoDB collection.
    """
    try:
        result = await Media.collection.delete_one({
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
