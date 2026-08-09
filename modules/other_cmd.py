from pyrogram import Client, filters

CLEAN_FILE_NAME = {}
CUSTOM_CAPTION_TEXT = {}

@Client.on_message(filters.private & filters.command(['clean_name']))
async def toggle_clean_name(bot, message):
    user_id = message.from_user.id
    parts = message.text.split(" ")
    if len(parts) != 2 or parts[1].lower() not in ["on", "off"]:
        return await message.reply("Usage: /clean_name on or /clean_name off")
    CLEAN_FILE_NAME[user_id] = (parts[1].lower() == "on")
    await message.reply(f"✅ CLEAN FILE NAME is now <b>{'ENABLED' if CLEAN_FILE_NAME[user_id] else 'DISABLED'}</b>")
   

@Client.on_message(filters.private & filters.command(['add_caption']))
async def add_custom_caption(bot, message):

    user_id = message.from_user.id

    try:
        caption = message.text.split(" ", 1)[1]
    except:
        return await message.reply(
            "Usage:\n/add_caption your text"
        )

    CUSTOM_CAPTION_TEXT[user_id] = caption

    await message.reply("✅ Custom Caption Saved")
    
