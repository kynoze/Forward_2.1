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
    result = await Media.collection.delete_one({'_id': str(data.file_id)})
    if result.deleted_count:
        print(f"[DB] Deleted {file_id}")
        return True
    print(f"[DB] Not found: {file_id}")
    return False
    
f = """
async def delete_data(data):
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
"""
