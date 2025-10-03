import logging
from motor.motor_asyncio import AsyncIOMotorClient
from config import Config

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

DATABASE_URI = Config.DATABASE_URI
DATABASE_NAME = "forward_media"
COLLECTION_NAME = "media-collection"

client = AsyncIOMotorClient(DATABASE_URI)
db = client[DATABASE_NAME]
collection = db[COLLECTION_NAME]


async def save_data(file_id: str, caption: str):
    """
    Save a message to the DB. Skips duplicates.
    """
    document = {
        "_id": file_id,
        "use": "forward",
        "caption": caption or "No Caption"
    }
    try:
        await collection.insert_one(document)
        logger.info(f"Message saved in DB: {file_id}")
    except Exception as e:
        if "duplicate key error" in str(e).lower():
            logger.warning(f"Already saved in DB: {file_id}")
        else:
            logger.exception(f"Error saving message {file_id}: {e}")


async def get_search_results(limit: int = 1, count_only: bool = False):
    """
    Fetch messages from the DB.
    :param limit: number of messages to fetch
    :param count_only: if True, only return total count
    """
    if count_only:
        return await collection.count_documents({"use": "forward"})
    cursor = collection.find({"use": "forward"}).sort("_id", 1).limit(limit)
    return await cursor.to_list(length=limit)


async def delete_message_data(file_id: str = None):
    """
    Delete messages from DB. If file_id is None, delete all.
    """
    if file_id:
        result = await collection.delete_one({"_id": file_id})
        logger.info(f"Deleted {result.deleted_count} document(s) with ID {file_id}")
    else:
        result = await collection.delete_many({})
        logger.info(f"Deleted all documents: {result.deleted_count}")
