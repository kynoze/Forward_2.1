from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, Message
from bot import app
from config import OWNER_ID
from database.utils import Data
from database import  get_chat, add_chat

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


@app.on_message(filters.private & filters.command(['set_channel']))
async def set_target_channel(bot, message):    
    #if OWNER_ID  not ((str(message.from_user.id) in Config.ADMINS) or (message.from_user.username in Config.ADMINS)):
        #return await message.reply("You Are Not Allowed To Use This UserBot")
    
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
