import logging, pytz, asyncio
from config import Config
from pyrogram import Client, filters
from pyrogram.errors import FloodWait
from datetime import datetime
from database import get_search_results, delete_message_data  # Updated for Motor 3.6+

logger = logging.getLogger(__name__)

IST = pytz.timezone('Asia/Kolkata')
MessageCount = 0
BOT_STATUS = "0"
status = set(int(x) for x in BOT_STATUS.split())
OWNER = Config.OWNER_ID

@Client.on_message(filters.command("status"))
async def count(bot, m):
    if 1 in status:
        await m.reply_text("Currently Bot is forwarding messages.")
    else:
        await m.reply_text("Bot is Idle now, You can start a task.")

@Client.on_message(filters.command('total'))
async def total(bot, message):
    if message.from_user.id not in OWNER:
        return await message.reply_text("Who the hell are you!!")
    msg = await message.reply("Counting total messages in DB...", quote=True)
    try:
        total = await get_search_results(count_only=True)
        await msg.edit(f'Total Messages: {total}')
    except Exception as e:
        await msg.edit(f'Error: {e}')

@Client.on_message(filters.command('cleardb'))
async def clrdb(bot, message):
    if message.from_user.id not in OWNER:
        return await message.reply_text("Who the hell are you!!")
    msg = await message.reply("Clearing files from DB...", quote=True)
    try:
        await delete_message_data()
        await msg.edit('Cleared DB')
    except Exception as e:
        await msg.edit(f'Error: {e}')

@Client.on_message(filters.command("forward"))
async def forward(bot, message):
    global MessageCount
    if message.from_user.id not in OWNER:
        return await message.reply_text("Who the hell are you!!")
    if 1 in status:
        await message.reply_text("A task is already running.")
        return

    m = await bot.send_message(chat_id=message.from_user.id, text="Started Forwarding....")
    status.add(1)

    try:
        while True:
            data = await get_search_results(limit=1)
            if not data:
                break  # No more messages to forward

            for msg in data:
                to_chat = Config.TO_CHANNEL
                file_id = msg['id']
                caption = msg.get('caption', '')

                try:
                    try:
                        await bot.send_cached_media(
                            chat_id=to_chat,
                            file_id=file_id,
                            caption=caption
                        )
                    except FloodWait as e:
                        await asyncio.sleep(e.value)
                        await bot.send_cached_media(
                            chat_id=to_chat,
                            file_id=file_id,
                            caption=caption
                        )

                    await asyncio.sleep(1)
                except Exception as e:
                    logger.exception(e)
                    continue

                # Delete from DB after forwarding
                try:
                    await delete_message_data(file_id)
                except Exception as e:
                    logger.exception(e)

                MessageCount += 1

                # Update status message
                try:
                    datetime_ist = datetime.now(IST)
                    ISTIME = datetime_ist.strftime("%I:%M:%S %p - %d %B %Y")
                    await m.edit(
                        f"Total Forwarded: <code>{MessageCount}</code>\n"
                        f"Forwarded Using: Bot\nSleeping for 1 second\nLast Forwarded at {ISTIME}"
                    )
                except Exception as e:
                    logger.exception(e)
                    await bot.send_message(chat_id=OWNER, text=f"LOG-Error: {e}")

        await m.edit(text=f'Successfully Forwarded {MessageCount} messages')
    except Exception as e:
        logger.exception(e)
        await bot.send_message(1985266909, f"LOG-Error: {e}")
    finally:
        status.discard(1)
        MessageCount = 0
