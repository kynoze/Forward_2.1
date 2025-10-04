from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, Message
from bot import app
from config import OWNER_ID
from database.utils import Data
from database import  get_chat, add_chat

@app.on_message(filters.command("help") & filters.private)
async def help_command(client: Client, message: Message):
    await message.reply(
        f"""
             <b> Bot Admin Commands</b>
             
        /index - Index files from channel.
        /total - Check total files in DB. 
        /cleardb - Clear all files from database.
        /status - Bot current status. 
        /set_channel - Set target channel.
        /forward - Start forwarding.
""",
        reply_markup=InlineKeyboardMarkup(
        [[
                InlineKeyboardButton("Source", url="https://github.com/lx0980/Forward_2.1"),
                InlineKeyboardButton("Channel", url="https://t.me/thelx0980")
            ]]))


@app.on_message(filters.command('total'))
async def total(bot, message):
    msg = await message.reply("Counting total messages in DB...", quote=True)
    try:
        total = await Data.count_documents()
        await msg.edit(f'Total Messages: {total}')
    except Exception as e:
        await msg.edit(f'Error: {e}')


@app.on_message(filters.private & filters.command(['set_channel']))
async def set_target_channel(bot, message):
    if message.from_user.id not in OWNER_ID:
        await message.reply_text("Who the hell are you!!")
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
