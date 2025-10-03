import re
import pytz
import logging
from datetime import datetime
from pyrogram import Client, filters
from pyrogram.enums import MessageMediaType
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup, CallbackQuery
from pyrogram.errors import FloodWait
from config import Config
from bot import Bot
from asyncio.exceptions import TimeoutError
from database import save_data

logger = logging.getLogger(__name__)
CHANNEL = {}
SKIN_NO = {}
END_MSG_ID = {}
IST = pytz.timezone('Asia/Kolkata')
OWNER = Config.OWNER_ID

@Client.on_message(filters.private & filters.command("index"))
async def run(bot, message):
    if message.from_user.id not in OWNER:
        await message.reply_text("Who the hell are you!!")
        return

    # Ask for channel link
    while True:
        try:
            chat = await bot.ask(
                text="To Index a channel send me public channel link like <code>https://t.me/xxxxx</code>",
                chat_id=message.from_user.id,
                filters=filters.text,
                timeout=30
            )
            channel = chat.text
        except TimeoutError:
            await bot.send_message(message.from_user.id, "Request timed out.\nRestart with /index")
            return

        if re.match(r"https://t.me/.*", channel, flags=re.IGNORECASE):
            break
        else:
            await chat.reply_text("Wrong URL. Try again.")
            continue

    # Extract chat username
    chat_usr = re.search(r"t.me/(.*)", channel).group(1)
    try:
        chat_obj = await bot.get_chat(chat_usr)
        CHANNEL[message.from_user.id] = chat_obj.username
    except Exception as e:
        logger.exception(e)
        await message.reply(f"Error: {e}")
        return

    # Ask for start SKIP_NO
    while True:
        try:
            skip_msg = await bot.ask(
                text="Send me from where you want to start forwarding. Send 0 for beginning.",
                chat_id=message.from_user.id,
                filters=filters.text,
                timeout=30
            )
        except TimeoutError:
            await bot.send_message(message.from_user.id, "Request timed out.\nRestart with /index")
            return

        try:
            SKIN_NO[message.from_user.id] = int(skip_msg.text)
            break
        except ValueError:
            await skip_msg.reply_text("Invalid ID. It should be an integer.")

    # Ask for ending message ID
    while True:
        try:
            end_msg = await bot.ask(
                text="Send me forward ending message ID",
                chat_id=message.from_user.id,
                filters=filters.text,
                timeout=30
            )
        except TimeoutError:
            await bot.send_message(message.from_user.id, "Request timed out.\nRestart with /index")
            return

        try:
            END_MSG_ID[message.from_user.id] = int(end_msg.text)
            break
        except ValueError:
            await end_msg.reply_text("Invalid ID. It should be an integer.")

    buttons = InlineKeyboardMarkup([
        [InlineKeyboardButton("Index Media", callback_data="index")],
        [InlineKeyboardButton("Cancel", callback_data="cancel")]
    ])

    await bot.send_message(
        chat_id=message.from_user.id,
        text="Ok, now choose what type of messages you want to forward.",
        reply_markup=buttons
    )


@Client.on_callback_query()
async def cb_handler(bot: Client, query: CallbackQuery):
    if query.data == "cancel":
        return await query.message.delete()

    filter_type = "media" if query.data == "index" else None
    await query.message.delete()

    m = await bot.send_message(chat_id=query.from_user.id, text="Indexing Started")
    user_id = query.from_user.id
    msg_count = 0
    mcount = 0
    deleted = 0
    unsupported = 0
    lst_msg_id = END_MSG_ID.get(user_id)
    chat = CHANNEL.get(user_id)
    CURRENT = SKIN_NO.get(user_id, 0)

    try:
        async for msg in bot.iter_messages(chat, lst_msg_id, CURRENT):
            if msg.empty:
                deleted += 1
                continue
            if not msg.media:
                unsupported += 1
                continue

            # Determine caption
            file_name = getattr(msg.video or msg.document or msg.audio, 'file_name', None)
            caption = msg.caption or file_name or "No Caption"

            # Get file_id if media
            id = None
            if filter_type == "media" and msg.media in [
                MessageMediaType.DOCUMENT,
                MessageMediaType.VIDEO,
                MessageMediaType.AUDIO,
                MessageMediaType.PHOTO
            ]:
                media = getattr(msg, msg.media.value, None)
                if media:
                    id = media.file_id

            if id:
                try:
                    await save_data(id, caption)
                except Exception as e:
                    logger.exception(e)
                    await bot.send_message(OWNER, f"LOG-Error: {e}")

            msg_count += 1
            mcount += 1
            new_skip_no = CURRENT + msg_count
            logger.info(f"Total Indexed: {msg_count} - Current SKIP_NO: {new_skip_no}")

            # Update progress every 100 messages
            if mcount == 100:
                try:
                    ISTIME = datetime.now(IST).strftime("%I:%M:%S %p - %d %B %Y")
                    await m.edit(
                        text=f"Total Indexed: <code>{msg_count}</code>\n"
                             f"Current skip_no: <code>{new_skip_no}</code>\n"
                             f"Deleted Msg skip: {deleted}\nLast edited at {ISTIME}"
                    )
                    mcount = 0
                except FloodWait as e:
                    logger.info(f"Floodwait {e.value}")
                except Exception as e:
                    logger.exception(e)
                    await bot.send_message(OWNER, f"LOG-Error: {e}")

        await m.edit(
            f"Successfully Indexed <code>{msg_count}</code> messages.\n\n"
            f"Non Media Files: {unsupported}\nDeleted Message: {deleted}"
        )

    except Exception as e:
        logger.exception(e)
        await m.edit(text=f"Error: {e}")
