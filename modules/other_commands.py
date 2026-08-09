from pyrogram import Client, filters

CLEAN_FILE_NAME= {}

@Client.on_message(filters.private & filters.command(['clean_name']))
async def toggle_clean_name(bot, message):
    user_id = message.from_user.id
    parts = message.text.split(" ")
    if len(parts) != 2 or parts[1].lower() not in ["on", "off"]:
        return await message.reply("Usage: /clean_name on or /clean_name off")
    CLEAN_FILE_NAME[user_id] = (parts[1].lower() == "on")
    await message.reply(f"✅ CLEAN FILE NAME is now <b>{'ENABLED' if CLEAN_FILE_NAME[user_id] else 'DISABLED'}</b>")
   
