import asyncio
import time
import logging
from typing import Any
from pyrogram import Client, filters, enums
from pyrogram.errors import FloodWait, RPCError
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from config import OWNER_ID, COLLECTION_NAME
from database.utils import temp, get_readable_time
from database import db
from bot import app
from database.utils import save_file

logger = logging.getLogger(__name__)
lock = asyncio.Lock()
temp.CANCEL = False
stats = {}  # per-user progress tracking

SUPPORTED_TYPES = (
    enums.MessageMediaType.VIDEO,
    enums.MessageMediaType.DOCUMENT,
    enums.MessageMediaType.AUDIO,
)

# -------------------- CALLBACK: INDEX START / CANCEL --------------------
@app.on_callback_query(filters.regex(r'^index#'))
async def index_files(bot: Client, query):
    parts = query.data.split("#")
    if len(parts) != 5:
        return await query.answer("⚠️ Invalid callback data!", show_alert=True)

    _, ident, chat, lst_msg_id, skip = parts
    msg = query.message

    if ident == 'yes':
        await msg.edit("<b>📦 Indexing Started!</b>\n\nCollecting files from channel...")
        try:
            chat = int(chat)
        except Exception:
            pass

        primary_col = db[COLLECTION_NAME]
        await index_files_to_db(
            int(lst_msg_id),
            chat,
            msg,
            bot,
            int(skip),
            primary_col,
            query.from_user.id
        )

    elif ident == 'cancel':
        temp.CANCEL = True
        await msg.edit("🛑 Cancelling indexing process...")


# -------------------- CALLBACK: STATUS --------------------
@app.on_callback_query(filters.regex(r"^index_progress_"))
async def index_progress_callback(client, query):
    try:
        user_id = int(query.data.split("_")[-1])
    except Exception:
        return await query.answer("⚠️ Invalid callback data!", show_alert=True)

    get_status = stats.get(user_id)
    if not get_status:
        return await query.answer("No active indexing task.", show_alert=True)

    text = (
        f"⚙️ Indexing Progress\n\n"
        f"🔢 Processed: {get_status['processed']}\n"
        f"✅ Saved: {get_status['total_files']}\n"
        f"♻️ Duplicates: {get_status['duplicate']}\n"
        f"🗑️ Deleted: {get_status['deleted']}\n"
        f"🚫 Skipped: {get_status['no_media']}\n"
        f"❌ Unsupported: {get_status['unsupported']}\n"
        f"⚠️ Errors: {get_status['errors']}"
    )
    await query.answer(text, show_alert=True)


# -------------------- COMMAND: /INDEX --------------------
@app.on_message(filters.command('index') & filters.private)
async def send_for_index(bot: Client, message: Any):
    if message.from_user.id not in OWNER_ID:
        return await message.reply_text("❌ You are not authorized!")

    if lock.locked():
        return await message.reply('⚠️ Another indexing process is running, please wait.')

    prompt = await message.reply("📩 Forward the last message from the channel or send a message link:")
    user_msg = await bot.listen(chat_id=message.chat.id, user_id=message.from_user.id)
    await prompt.delete()

    # Support forwarded message or t.me link
    if getattr(user_msg, "text", None) and user_msg.text.startswith("https://t.me"):
        try:
            msg_link = user_msg.text.split("/")
            last_msg_id = int(msg_link[-1])
            chat_id = msg_link[-2]
            chat_id = int("-100" + chat_id) if chat_id.isnumeric() else chat_id
        except Exception:
            return await message.reply('❌ Invalid link format!')
    elif getattr(user_msg, "forward_from_chat", None) and user_msg.forward_from_chat.type == enums.ChatType.CHANNEL:
        last_msg_id = user_msg.forward_from_message_id
        chat_id = user_msg.forward_from_chat.username or user_msg.forward_from_chat.id
    else:
        return await message.reply('❌ Invalid message! Must be a forwarded channel message or t.me link.')

    try:
        chat = await bot.get_chat(chat_id)
    except Exception as e:
        return await message.reply(f'❌ Error: {e}')

    if chat.type not in [enums.ChatType.CHANNEL, enums.ChatType.GROUP, enums.ChatType.SUPERGROUP]:
        return await message.reply("❌ I can only index channels & groups!")

    # Ask for number of messages to skip
    s = await message.reply("✏️ Enter number of messages to skip from start:")
    skip_msg = await bot.listen(chat_id=message.chat.id, user_id=message.from_user.id)
    await s.delete()

    try:
        skip = int(skip_msg.text)
    except Exception:
        return await message.reply("❌ Invalid number!")

    buttons = [
        [InlineKeyboardButton("✅ START", callback_data=f'index#yes#{chat.id}#{last_msg_id}#{skip}')],
        [InlineKeyboardButton("❌ CANCEL", callback_data=f'index#cancel#{chat.id}#{last_msg_id}#{skip}')]
    ]

    await message.reply(
        f'<b>📚 Indexing Confirmation</b>\n\n'
        f'📌 Channel: {chat.title}\n'
        f'📝 Last message id: <code>{last_msg_id}</code>\n'
        f'⏩ Skip First: <code>{skip}</code>\n'
        f'📂 To Index: <code>{last_msg_id - skip if last_msg_id > skip else 0}</code>',
        reply_markup=InlineKeyboardMarkup(buttons)
    )


# -------------------- INDEXING FUNCTION --------------------
async def index_files_to_db(lst_msg_id: int, chat: Any, msg: Any, bot: Client, skip: int, primary_col, user_id: int) -> None:
    start_time = time.time()
    stats[user_id] = {
        'processed': 0,
        'total_files': 0,
        'duplicate': 0,
        'errors': 0,
        'deleted': 0,
        'no_media': 0,
        'unsupported': 0
    }

    total_to_index = max(0, lst_msg_id - skip)
    if total_to_index <= 0:
        await msg.edit("⚠️ No messages to index after skipping!")
        return

    try:
        await msg.edit(
            "📦 Starting to index media...",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("📊 Status", callback_data=f"index_progress_{user_id}"),
                InlineKeyboardButton("🚫 Cancel", callback_data=f"index#cancel#{chat}#{lst_msg_id}#{skip}")
            ]])
        )
    except RPCError:
        pass

    async with lock:
        while True:
            try:
                async for message in bot.iter_messages(chat, lst_msg_id, skip if skip else 0):
                    if temp.CANCEL:
                        temp.CANCEL = False
                        duration = get_readable_time(time.time() - start_time)
                        await msg.edit(
                            f"🛑 <b>Indexing Cancelled!</b>\n\n"
                            f"🔢 Processed: {stats[user_id]['processed']}\n"
                            f"✅ Saved: {stats[user_id]['total_files']}\n"
                            f"♻️ Duplicates: {stats[user_id]['duplicate']}\n"
                            f"🗑️ Deleted: {stats[user_id]['deleted']}\n"
                            f"🚫 No Media: {stats[user_id]['no_media']}\n"
                            f"❌ Unsupported: {stats[user_id]['unsupported']}\n"
                            f"⚠️ Errors: {stats[user_id]['errors']}\n"
                            f"⏳ Duration: {duration}"
                        )
                        stats.pop(user_id, None)
                        return

                    stats[user_id]['processed'] += 1

                    if not message or not message.media:
                        stats[user_id]['no_media'] += 1
                        continue

                    if message.media not in SUPPORTED_TYPES:
                        stats[user_id]['unsupported'] += 1
                        continue

                    media = getattr(message, message.media.value, None)
                    if not media:
                        stats[user_id]['no_media'] += 1
                        continue

                    media.caption = message.caption
                    try:
                        result = await save_file(media, primary_col)
                        if result == 'suc':
                            stats[user_id]['total_files'] += 1
                        elif result == 'dup':
                            stats[user_id]['duplicate'] += 1
                        else:
                            stats[user_id]['errors'] += 1
                    except FloodWait as e:
                        wait = int(getattr(e, "value", 5)) + 2
                        await msg.edit(f"⏳ FloodWait during save_file. Sleeping {wait}s...")
                        await asyncio.sleep(wait)
                    except Exception:
                        stats[user_id]['errors'] += 1
                        logger.exception("Error saving media")

                # Completed
                duration = get_readable_time(time.time() - start_time)
                await msg.edit(
                    f"🎉 <b>Indexing Completed!</b>\n\n"
                    f"🔢 Processed: {stats[user_id]['processed']}\n"
                    f"✅ Saved: {stats[user_id]['total_files']}\n"
                    f"♻️ Duplicates: {stats[user_id]['duplicate']}\n"
                    f"🗑️ Deleted: {stats[user_id]['deleted']}\n"
                    f"🚫 Skipped: {stats[user_id]['no_media']}\n"
                    f"❌ Unsupported: {stats[user_id]['unsupported']}\n"
                    f"⚠️ Errors: {stats[user_id]['errors']}\n"
                    f"⏳ Duration: {duration}"
                )
                stats.pop(user_id, None)
                return

            except FloodWait as e:
                wait = int(getattr(e, "value", 5)) + 2
                logger.warning("FloodWait triggered: sleeping %ds", wait)
                await asyncio.sleep(wait)
                continue

            except Exception as e:
                logger.exception("Indexing failed: %s", e)
                try:
                    await msg.reply(f'❌ Indexing failed: {str(e)}')
                except Exception:
                    pass
                stats.pop(user_id, None)
                return
