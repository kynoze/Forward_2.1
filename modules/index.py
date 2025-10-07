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

SUPPORTED_TYPES = (enums.MessageMediaType.VIDEO, enums.MessageMediaType.DOCUMENT)
progress_data = {}  # user_id -> dict storing current stats


@app.on_message(filters.command('index') & filters.private)
async def send_for_index(bot: Client, message: Any):
    if message.from_user.id not in OWNER_ID:
        return await message.reply_text("Who the hell are you!!")

    if lock.locked():
        return await message.reply('⚠️ Please wait until current process completes.')

    prompt = await message.reply("📩 Forward the last message from channel or send message link")
    user_msg = await bot.listen(chat_id=message.chat.id, user_id=message.from_user.id)
    await prompt.delete()

    # support either a t.me link or a forwarded channel message
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
        return await message.reply('❌ Invalid message! Must be forwarded channel message or link.')

    try:
        chat = await bot.get_chat(chat_id)
    except Exception as e:
        return await message.reply(f'❌ Error: {e}')

    if chat.type != enums.ChatType.CHANNEL:
        return await message.reply("❌ I can only index channels!")

    s = await message.reply("✏️ Enter number of messages to skip from start:")
    skip_msg = await bot.listen(chat_id=message.chat.id, user_id=message.from_user.id)
    await s.delete()

    try:
        skip = int(skip_msg.text)
    except Exception:
        return await message.reply("❌ Invalid number!")

    # ✅ Confirmation buttons: Start / Cancel
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


@app.on_callback_query(filters.regex(r'^index#yes'))
async def start_indexing(bot: Client, query):
    _, _, chat_id, last_msg_id, skip = query.data.split("#")
    user_id = query.from_user.id
    skip = int(skip)
    last_msg_id = int(last_msg_id)
    chat_id = int(chat_id) if chat_id.isdigit() else chat_id

    try:
        chat = await bot.get_chat(chat_id)
    except Exception as e:
        return await query.message.reply(f'❌ Error: {e}')

    # Initial progress button
    progress_buttons = [
        [InlineKeyboardButton("📊 Progress", callback_data=f'progress')],
        [InlineKeyboardButton("🚫 Cancel", callback_data=f'index#cancel#{chat_id}#{last_msg_id}#{skip}')]
    ]
    progress_msg = await query.message.edit_text(
        "<b>📦 Indexing Started!</b>\n\nCollecting files from channel...",
        reply_markup=InlineKeyboardMarkup(progress_buttons)
    )

    primary_col = db[COLLECTION_NAME]
    progress_data[user_id] = {
        'processed': 0,
        'saved': 0,
        'duplicates': 0,
        'errors': 0,
        'deleted': 0,
        'no_media': 0,
        'unsupported': 0,
        'sleeping': None,
        'msg_obj': progress_msg
    }

    await index_files_to_db(last_msg_id, chat, user_id, bot, skip, primary_col)


@app.on_callback_query(filters.regex(r'^progress$'))
async def progress_callback(client, query):
    user_id = query.from_user.id
    data = progress_data.get(user_id)
    if not data:
        await query.answer("No progress yet", show_alert=True)
        return

    text = (
        f"📊 <b>Current Indexing Progress</b>\n\n"
        f"🔢 Processed: {data['processed']}\n"
        f"✅ Saved: {data['saved']}\n"
        f"♻️ Duplicates: {data['duplicates']}\n"
        f"🗑️ Deleted: {data['deleted']}\n"
        f"🚫 No Media: {data['no_media']}\n"
        f"❌ Unsupported: {data['unsupported']}\n"
        f"⚠️ Errors: {data['errors']}"
    )
    if data.get("sleeping"):
        text += f"\n⏳ Sleeping for {data['sleeping']}s..."
    await query.answer(text, show_alert=True)


@app.on_callback_query(filters.regex(r'^index#cancel'))
async def cancel_indexing(client, query):
    user_id = query.from_user.id
    temp.CANCEL = True
    data = progress_data.get(user_id)
    if data:
        try:
            await data['msg_obj'].edit_reply_markup(None)
        except Exception:
            pass
        stats = data.copy()
        del stats['msg_obj']
        text = "🛑 <b>Indexing Cancelled!</b>\n\n" + "\n".join([f"{k}: {v}" for k, v in stats.items()])
        await query.message.reply(text)
    await query.answer("Cancelling indexing...", show_alert=True)


async def index_files_to_db(lst_msg_id: int, chat: Any, user_id: int, bot: Client, skip: int, primary_col) -> None:
    start_time = time.time()
    data = progress_data[user_id]

    async with lock:
        async for message in bot.iter_messages(chat, lst_msg_id, skip if skip else 0):
            if temp.CANCEL:
                temp.CANCEL = False
                stats = data.copy()
                del stats['msg_obj']
                text = "🛑 <b>Indexing Cancelled!</b>\n\n" + "\n".join([f"{k}: {v}" for k, v in stats.items()])
                try:
                    await data['msg_obj'].edit_reply_markup(None)
                    await bot.send_message(chat.id, text)
                except Exception:
                    pass
                return

            data['processed'] += 1

            msg_id = getattr(message, "message_id", None) or getattr(message, "id", None)
            if msg_id is not None and msg_id <= skip:
                continue

            if not message.media:
                data['no_media'] += 1
            elif message.media not in SUPPORTED_TYPES:
                data['unsupported'] += 1
            else:
                media = getattr(message, message.media.value, None)
                mime = getattr(media, "mime_type", "") if media else ""
                if not media or not mime.startswith("video"):
                    data['unsupported'] += 1
                else:
                    media.caption = message.caption
                    try:
                        result = await save_file(media, primary_col)
                        if result == 'suc':
                            data['saved'] += 1
                        elif result == 'dup':
                            data['duplicates'] += 1
                        else:
                            data['errors'] += 1
                    except FloodWait as e:
                        wait = int(getattr(e, "value", 5))
                        data['sleeping'] = wait
                        await asyncio.sleep(wait)
                        data['sleeping'] = None
                    except Exception:
                        data['errors'] += 1
                        logger.exception("Error saving media")

        # Completed
        duration = get_readable_time(time.time() - start_time)
        stats = data.copy()
        del stats['msg_obj']
        text = "🎉 <b>Indexing Completed!</b>\n\n" + "\n".join([f"{k}: {v}" for k, v in stats.items()])
        try:
            await data['msg_obj'].edit_reply_markup(None)
            await bot.send_message(chat.id, text)
        except Exception:
            pass
        progress_data.pop(user_id, None)
