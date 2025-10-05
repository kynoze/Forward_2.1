import time
from pyrogram import Client
from motor.motor_asyncio import AsyncIOMotorClient
from typing import Union, Optional, AsyncGenerator
from pyrogram import types

import config

# MongoDB connection
db = AsyncIOMotorClient(config.MONGO_URL).Anonymous

# Uptime tracking
START_TIME = time.time()


class Bot(Client):
    def __init__(self):
        super().__init__(
            name="MoviesBot",
            api_id=config.API_ID,
            api_hash=config.API_HASH,
            bot_token=config.TG_BOT_TOKEN,
            max_concurrent_transmissions=7,
        )

    async def start(self, *args, **kwargs):
        await super().start(*args, **kwargs)
        me = await self.get_me()
        self.id = me.id
        self.name = me.first_name
        self.username = me.username
   

    async def stop(self, *args, **kwargs):
        await super().stop(*args, **kwargs)

    async def iter_messages(self, chat_id: Union[int, str], limit: int, offset: int = 0) -> Optional[AsyncGenerator["types.Message", None]]:
        """Iterate through a chat sequentially.
        This convenience method does the same as repeatedly calling :meth:`~pyrogram.Client.get_messages` in a loop, thus saving
        you from the hassle of setting up boilerplate code. It is useful for getting the whole chat messages with a
        single call.
        Parameters:
            chat_id (``int`` | ``str``):
                Unique identifier (int) or username (str) of the target chat.
                For your personal cloud (Saved Messages) you can simply use "me" or "self".
                For a contact that exists in your Telegram address book you can use his phone number (str).
                
            limit (``int``):
                Identifier of the last message to be returned.
                
            offset (``int``, *optional*):
                Identifier of the first message to be returned.
                Defaults to 0.
        Returns:
            ``Generator``: A generator yielding :obj:`~pyrogram.types.Message` objects.
        Example:
            .. code-block:: python
                for message in app.iter_messages("pyrogram", 1, 15000):
                    print(message.text)
        """
        current = offset
        while True:
            new_diff = min(200, limit - current)
            if new_diff <= 0:
                return
            messages = await self.get_messages(chat_id, list(range(current, current+new_diff+1)))
            for message in messages:
                yield message
                current += 1
  


app = Bot()
