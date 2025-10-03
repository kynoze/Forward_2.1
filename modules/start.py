from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, Message
from bot import app
from database.utils import Data

@app.on_message(filters.command("help") & filters.private)
async def help_command(client: Client, message: Message):
    await message.reply_text(
        f"""This text is from help command
        ------->
""",
        reply_to_message_id=message.id
    )


@app.on_message(filters.command('total'))
async def total(bot, message):
    #if message.from_user.id not in OWNER:
       # return await message.reply_text("Who the hell are you!!")
    msg = await message.reply("Counting total messages in DB...", quote=True)
    try:
        total = await Data.count_documents()
        await msg.edit(f'Total Messages: {total}')
    except Exception as e:
        await msg.edit(f'Error: {e}')
