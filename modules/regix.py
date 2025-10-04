import os
import sys 
import math
import time, re
import asyncio 

async def copy_msg(msg, bot, message, chat_id):
   try:
     await bot.send_cached_media(
         chat_id=sts.get('TO'),
         file_id=msg.file_id,
         caption=msg.caption)
   except FloodWait as e:
     await asyncio.sleep(e.value) 
     await copy_msg(msg, bot, message, chat_id)
   except Exception as e:
     print(e)

async def delete_data(data):
    await Data.collection.delete_one({
        'use': data.use,
        'file_id': data.file_id,
        'caption': data.caption
    })
    
def media(msg):
  if msg.media:
     media = getattr(msg, msg.media.value, None)
     if media:
        return getattr(media, 'file_id', None)
  return None 
