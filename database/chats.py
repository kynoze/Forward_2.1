from . import chatsdb

async def add_chat(chat_id):
    """Store only one chat — only chat_id."""
    await chatsdb.delete_many({})  # Remove any existing chat
    await chatsdb.insert_one({"chat_id": chat_id})
    
async def remove_chat(chat_id):
    """ Remove a chat from the database when bot leaves or is removed."""
    await chatsdb.delete_one({"chat_id": chat_id})

async def get_chat():
    """Return only the current chat_id."""
    chat = await chatsdb.find_one({})
    if chat:
        return chat["chat_id"]
    return None 
