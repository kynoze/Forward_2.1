from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, Message
from bot import app
from config import OWNER_ID
from database.utils import Data
from database import  get_chat, add_chat

@app.on_message(filters.command("help") & filters.private)
async def help_command(client: Client, message: Message):
    await message.reply_text(
        f"""
        /index - index files from channel
        /total - total files in DB. 
        /cleardb - clear all files from database.
        /status - bot current status. 
        /set_channel - set target channel. 
""",
        reply_to_message_id=message.id
    )


@app.on_message(filters.command('total'))
async def total(bot, message):
    msg = await message.reply("Counting total messages in DB...", quote=True)
    try:
        total = await Data.count_documents()
        await msg.edit(f'Total Messages: {total}')
    except Exception as e:
        await msg.edit(f'Error: {e}')


@app.on_message(filters.private & filters.command(['set_channel']) & filters.user(OWNER_ID))
async def set_target_channel(bot, message):
    try:
        _, chat_id = message.text.split(" ")
    except:
        return await message.reply("Give me a target channel ID")
    try:
        chat_id = int(chat_id)
    except:
        return await message.reply("Give me a valid ID")

    try:
        chat = await bot.get_chat(chat_id)
    except:
        return await message.reply("Make me a admin in your target channel.")
    add_chat(int(chat.id))
    await message.reply(f"Successfully set {chat.title} target channel.")
