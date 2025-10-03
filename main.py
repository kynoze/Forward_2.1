import asyncio
import importlib
import sys
import config

from pyrogram import idle, errors
from pyrogram.enums import ChatMemberStatus

from bot import app
from modules import ALL_MODULES
from f_logging import LOGGER


async def boot():
    LOGGER(__name__).info("Bot is starting...")
    await app.start()
    LOGGER(__name__).info("Bot started successfully.")

    for module in ALL_MODULES:
        importlib.import_module(f"modules.{module}")

    try:
        await idle()
    finally:
        LOGGER(__name__).warning("Bot is shutting down...")
        await app.stop()


if __name__ == "__main__":
    try:
        asyncio.get_event_loop().run_until_complete(boot())
    except KeyboardInterrupt:
        LOGGER(__name__).warning("Bot interrupted by user or system.")
