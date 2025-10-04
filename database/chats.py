from . import chatsdb

async def add_chat(chat_id):
    """
    Adds a chat to the database if it doesn't already exist.
    """
    if not await chatsdb.find_one({"chat_id": chat_id}):
        await chatsdb.insert_one({"chat_id": chat_id})

async def remove_chat(chat_id):
    """
    Remove a chat from the database when bot leaves or is removed.
    """
    await chatsdb.delete_one({"chat_id": chat_id})
