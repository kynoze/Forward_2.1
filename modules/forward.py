# plugins/forward.py
import logging
import asyncio
import pytz
from datetime import datetime

from pyrogram import Client, filters
from pyrogram.errors import FloodWait

from config import OWNER_ID, TO_CHANNEL
from database.utils import get_search_results, Data  # Data is uMongo Document class

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

IST = pytz.timezone("Asia/Kolkata")
MessageCount = 0
status = set()          # simple set to avoid overlapping runs

def is_owner(user_id: int) -> bool:
    if isinstance(OWNER, (list, tuple, set)):
        return user_id in OWNER
    return user_id == OWNER


@Client.on_message(filters.command("forward"))
async def forward(bot: Client, message):
    """
    Hybrid forwarding:
      1) try send_cached_media using stored file_id
      2) fallback to copy_message using channel_id + message_id
    """
    global MessageCount

    if not is_owner(message.from_user.id):
        return await message.reply_text("Who the hell are you!!")

    if 1 in status:
        return await message.reply_text("A task is already running.")
    status.add(1)
    MessageCount = 0

    status_msg = await bot.send_message(chat_id=message.from_user.id, text="🚀 Started Forwarding...")

    try:
        # loop while there are docs to forward
        while await Data.collection.count_documents({"use": "forward"}) > 0:
            rows = await get_search_results()  # expecting a list of Data documents (limit=1 in your get_search_results)
            if not rows:
                break

            for doc in rows:
                # robust extraction of fields from uMongo Document
                try:
                    doc_id = getattr(doc, "id", None) or getattr(doc, "_id", None) or getattr(doc, "_data", {}).get("_id")
                    file_id = doc_id  # your DB stores file_id as _id
                    caption = getattr(doc, "caption", None) or getattr(doc, "_data", {}).get("caption", "") or ""
                    channel_id = getattr(doc, "channel_id", None) or getattr(doc, "_data", {}).get("channel_id")
                    message_id = getattr(doc, "message_id", None) or getattr(doc, "_data", {}).get("message_id")
                except Exception:
                    logger.exception("Failed to read DB doc fields, removing problematic doc to avoid blocking.")
                    # try to remove problematic doc
                    try:
                        if doc_id:
                            await Data.collection.delete_one({"_id": doc_id})
                    except Exception:
                        logger.exception("Failed to delete problematic doc.")
                    continue

                if not file_id:
                    logger.warning("Skipping DB entry without file id; deleting it to avoid blocking.")
                    try:
                        await Data.collection.delete_one({"_id": doc_id})
                    except Exception:
                        logger.exception("Failed to delete doc without id.")
                    continue

                to_chat = TO_CHANNEL

                # Try send_cached_media first, then fallback to copy_message
                sent_ok = False
                try:
                    try:
                        await bot.send_cached_media(chat_id=to_chat, file_id=file_id, caption=caption)
                        sent_ok = True
                    except FloodWait as fw:
                        logger.info(f"FloodWait when send_cached_media: sleeping {fw.value}s")
                        await asyncio.sleep(fw.value)
                        await bot.send_cached_media(chat_id=to_chat, file_id=file_id, caption=caption)
                        sent_ok = True
                    except Exception as e_cached:
                        # fallback to copy_message
                        logger.warning(f"send_cached_media failed for {file_id}: {e_cached}; trying copy_message fallback.")
                        # proceed to fallback below
                except Exception as outer_e:
                    logger.exception(f"Unexpected error while trying send_cached_media for {file_id}: {outer_e}")

                if not sent_ok:
                    # fallback to copy_message using channel_id + message_id
                    if channel_id and message_id:
                        try:
                            try:
                                # channel_id might be username or int-string. Try converting if numeric.
                                from_chat = int(channel_id) if isinstance(channel_id, (int, str)) and str(channel_id).lstrip("-").isnumeric() else channel_id
                                msg_id_int = int(message_id)
                                await bot.copy_message(chat_id=to_chat, from_chat_id=from_chat, message_id=msg_id_int, caption=caption or None)
                                sent_ok = True
                            except FloodWait as fw2:
                                logger.info(f"FloodWait when copy_message: sleeping {fw2.value}s")
                                await asyncio.sleep(fw2.value)
                                await bot.copy_message(chat_id=to_chat, from_chat_id=from_chat, message_id=msg_id_int, caption=caption or None)
                                sent_ok = True
                        except Exception as e_copy:
                            logger.exception(f"Fallback copy_message failed for {file_id} (from {channel_id}/{message_id}): {e_copy}")
                            # do not delete DB entry — allow manual retry later
                    else:
                        logger.warning(f"No channel_id/message_id for fallback for {file_id}; will keep DB entry for manual handling.")

                if not sent_ok:
                    # If both methods failed, skip deletions and continue to next doc
                    continue

                # Delete the successfully forwarded entry from DB (by exact _id)
                try:
                    await Data.collection.delete_one({"_id": file_id})
                except Exception as del_exc:
                    logger.exception(f"Failed to delete forwarded doc {file_id} from DB: {del_exc}")

                MessageCount += 1

                # update progress every 10 forwards to avoid frequent edits
                if MessageCount % 10 == 0:
                    try:
                        now = datetime.now(IST).strftime("%I:%M:%S %p - %d %B %Y")
                        await status_msg.edit(
                            f"📤 Total Forwarded: <code>{MessageCount}</code>\n"
                            f"Sleeping for 1s\n"
                            f"Last Forwarded at {now}"
                        )
                    except Exception:
                        logger.exception("Failed to update progress message")

                # small safe delay
                await asyncio.sleep(1)

        # finished - show final count
        try:
            await status_msg.edit(text=f"✅ Successfully Forwarded {MessageCount} messages")
        except Exception:
            logger.exception("Failed to edit final status message")

    except Exception as outer:
        logger.exception(f"Forwarding loop crashed: {outer}")
        # notify owner(s)
        if isinstance(OWNER, (list, tuple, set)):
            for oid in OWNER:
                try:
                    await bot.send_message(oid, f"LOG-Error: {outer}")
                except Exception:
                    pass
        else:
            try:
                await bot.send_message(OWNER, f"LOG-Error: {outer}")
            except Exception:
                pass

    finally:
        status.discard(1)
        MessageCount = 0
