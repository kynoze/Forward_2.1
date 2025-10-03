from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, Message
from bot import app

@app.on_message(filters.command("help") & filters.private)
async def help_command(client: Client, message: Message):
    await message.reply_text(
        f"""This text is from help command
        ------->
""",
        reply_to_message_id=message.id
    )
