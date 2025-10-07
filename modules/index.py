import asyncio
import time
import logging
from typing import Any
from pyrogram import Client, filters, enums
from pyrogram.errors import FloodWait, RPCError
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from config import OWNER_ID, COLLECTION_NAME
from database.utils import temp, get_readable_time  # save_file moved to files.py; we'll import files.save_file below
from database import db
from bot import app
from database.utils import save_file  # import the save_file implementation from files.py

logger = logging.getLogger(__name__)
lock = asyncio.Lock()
temp.CANCEL = False
stats = {}  # global dict to track progress per user

SUPPORTED_TYPES = (
    enums.MessageMediaType.VIDEO,
    enums.MessageMediaType.DOCUMENT,
    enums.MessageMediaType.AUDIO,
)


@app.on_callback_query(filters.regex(r'^index'))
async def index_files(bot: Client, query):
    _, ident, chat, lst_msg_id, skip = query.data.split("#")
    msg = query.message

    if ident == 'yes':
        await msg.edit("<b>📦 Indexing Started!</b>\n\nCollecting files from channel...")
        try:
            chat = int(chat)
        except Exception:
            pass

        primary_col = db[COLLECTION_NAME]
        await index_files_to_db(int(lst_msg_id), chat, msg, bot, int(skip), primary_col)

    elif ident == 'cancel':
        temp.CANCEL = True
        await msg.edit("🛑 Cancelling indexing process...")


@app.on_callback_query(filters.regex(r"^check_progress_(\d+)$"))
async def check_progress_callback(client, callback_query):
    if callback_query.from_user.id not in OWNER_ID:
        return await callback_query.answer("Not allowed!", show_alert=True)

    user_id = int(callback_query.matches[0].group(1))
    get_status = stats.get(user_id)

    if not get_status:
        return await callback_query.answer("No active indexing task.", show_alert=True)

    text = (
        f"⚙️ <b>Indexing Progress</b>\n\n"
        f"🔢 Processed: <code>{get_status['processed']}</code>\n"
        f"✅ Saved: <code>{get_status['total_files']}</code>\n"
        f"♻️ Duplicates: <code>{get_status['duplicate']}</code>\n"
        f"🗑️ Deleted: <code>{get_status['deleted']}</code>\n"
        f"🚫 Skipped: <code>{get_status['no_media']}</code>\n"
        f"❌ Unsupported: <code>{get_status['unsupported']}</code>\n"
        f"⚠️ Errors: <code>{get_status['errors']}</code>"
    )

    await callback_query.answer(text, show_alert=True)


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


async def index_files_to_db(lst_msg_id: int, chat: Any, msg: Any, bot: Client, skip: int, primary_col) -> None:
    """
    Indexing loop using a single Mongo collection (primary_col).
    """
    start_time = time.time()
    user_id = msg.from_user.id

    # initialize per-user progress tracking
    stats[user_id] = {
        'processed': 0,
        'total_files': 0,
        'duplicate': 0,
        'errors': 0,
        'deleted': 0,
        'no_media': 0,
        'unsupported': 0
    }

    try:
        total_to_index = max(0, int(lst_msg_id) - int(skip))
    except Exception:
        await msg.edit("❌ Invalid lst_msg_id or skip.")
        return

    if total_to_index <= 0:
        await msg.edit("⚠️ No messages to index after skipping!")
        return

    try:
        await msg.edit(
            "📦 Starting to index media...",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("📊 Status", callback_data=f"check_progress_{user_id}"),
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
                            f"🔢 Processed: <code>{stats[user_id]['processed']}</code>\n"
                            f"✅ Saved: <code>{stats[user_id]['total_files']}</code>\n"
                            f"♻️ Duplicates: <code>{stats[user_id]['duplicate']}</code>\n"
                            f"🗑️ Deleted: <code>{stats[user_id]['deleted']}</code>\n"
                            f"🚫 No Media: <code>{stats[user_id]['no_media']}</code>\n"
                            f"❌ Unsupported: <code>{stats[user_id]['unsupported']}</code>\n"
                            f"⚠️ Errors: <code>{stats[user_id]['errors']}</code>\n"
                            f"⏳ Duration: <code>{duration}</code>"
                        )
                        stats.pop(user_id, None)
                        return

                    stats[user_id]['processed'] += 1

                    if not message:
                        stats[user_id]['deleted'] += 1
                        continue

                    if not message.media:
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

                # finished successfully
                duration = get_readable_time(time.time() - start_time)
                await msg.edit(
                    f"🎉 <b>Indexing Completed!</b>\n\n"
                    f"🔢 Processed: <code>{stats[user_id]['processed']}</code>\n"
                    f"✅ Saved: <code>{stats[user_id]['total_files']}</code>\n"
                    f"♻️ Duplicates: <code>{stats[user_id]['duplicate']}</code>\n"
                    f"🗑️ Deleted: <code>{stats[user_id]['deleted']}</code>\n"
                    f"🚫 Skipped: <code>{stats[user_id]['no_media']}</code>\n"
                    f"❌ Unsupported: <code>{stats[user_id]['unsupported']}</code>\n"
                    f"⚠️ Errors: <code>{stats[user_id]['errors']}</code>\n"
                    f"⏳ Duration: <code>{duration}</code>"
                )
                stats.pop(user_id, None)
                return

            except FloodWait as e:
                wait = int(getattr(e, "value", 5)) + 2
                logger.warning("FloodWait triggered while iterating: sleeping %ds", wait)
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
