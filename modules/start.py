from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, Message
from bot import app
from config import OWNER_ID
from database.utils import Media
from database import get_chat, add_chat
from modules.forward import forward_lock

@app.on_message(filters.command("help") & filters.private)
async def help_command(client: Client, message: Message):
    text = (
        "<b>🤖 Bot Admin Commands</b>\n\n"
        "/index - Index files from channel\n"
        "/total - Check total files in DB\n"
        "/cleardb - Clear all files from database\n"
        "/status - Bot current status\n"
        "/set_channel - Set target channel\n"
        "/forward - Start forwarding\n"
    )

    buttons = [
        [
            InlineKeyboardButton("🌐 Source", url="https://github.com/lx0980/Forward_2.1"),
            InlineKeyboardButton("📢 Channel", url="https://t.me/thelx0980")
        ]
    ]

    await message.reply(text, reply_markup=InlineKeyboardMarkup(buttons))


@app.on_message(filters.command('total') & filters.private)
async def total(bot, message):
    if message.from_user.id not in OWNER_ID:
        return await message.reply_text("Who the hell are you!!")

    msg = await message.reply("Counting total messages in DB...", quote=True)
    try:
        total = await Media.count_documents()
        await msg.edit(f'Total Messages in DB: <b>{total}</b>')
    except Exception as e:
        await msg.edit(f'Error: {e}')


@app.on_message(filters.private & filters.command(['set_channel']))
async def set_target_channel(bot, message):
    if message.from_user.id not in OWNER_ID:
        return await message.reply_text("Who the hell are you!!")

    try:
        _, chat_id = message.text.split(" ")
        chat_id = int(chat_id)
    except:
        return await message.reply("⚠️ Usage: <code>/set_channel chat_id</code>")

    try:
        chat = await bot.get_chat(chat_id)
    except Exception as e:
        return await message.reply(f"Make me admin in that channel first.\nError: {e}")

    await add_chat(int(chat.id))
    await message.reply(f"✅ Successfully set <b>{chat.title}</b> as target channel.")

@app.on_message(filters.private & filters.command("cleardb"))
async def clear_database(bot, message):
    if message.from_user.id not in OWNER_ID:
        return await message.reply_text("Who the hell are you!!")

    msg = await message.reply("🗑 Clearing database...")
    try:
        deleted = await Media.collection.delete_many({})
        await msg.edit(f"✅ Database cleared.\nDeleted documents: {deleted.deleted_count}")
    except Exception as e:
        await msg.edit(f"❌ Error: {e}")

@app.on_message(filters.private & filters.command("status"))
async def status_command(bot, message):
    if message.from_user.id not in OWNER_ID:
        return await message.reply_text("Who the hell are you!!")
    if forward_lock.locked():  # <-- FIXED status check
        status_text = 'Bot is currently forwarding files'
    else:
        status_text = 'Bot is free, You can start new task'
    await message.reply_text(status_text)
