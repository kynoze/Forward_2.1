import asyncio
from pyrogram.errors import FloodWait
from database.utils import Media

async def copy_msg(msg, bot, message, chat_id, m, MessageCount):
   try:                             
       await bot.send_cached_media(
           chat_id=int(chat_id),
           file_id=msg.file_id,
           caption=msg.caption)
       return True
   except FloodWait as e:
     await m.edit_text(
         f"Total Forwarded: <code>{MessageCount}</code>\n"
         f"Sleeping for <code>{e.value}</code> second"
     )
     await asyncio.sleep(e.value)
     await copy_msg(msg, bot, message, chat_id, m, MessageCount)
   except Exception as e:
     print(e)
     return False

async def delete_data(data):
    result = await Media.collection.delete_one({
        'use': 'forward'
    })
    if result.deleted_count:
        print(f"[DB] Deleted {data.file_id}")
        return True
    print(f"[DB] Not found: {data.file_id}")
    return False
    
