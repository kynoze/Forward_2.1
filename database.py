import logging
from pymongo.errors import DuplicateKeyError
from umongo import Instance, Document, fields
from motor.motor_asyncio import AsyncIOMotorClient
from marshmallow import ValidationError
from config import Config

# ---------------------------
# Logger setup
# ---------------------------
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# ---------------------------
# Database configuration
# ---------------------------
DATABASE_URI = Config.DATABASE_URI
DATABASE_NAME = "forward_media"
COLLECTION_NAME = "media-collection"

# Async MongoDB client
client = AsyncIOMotorClient(DATABASE_URI)
database = client[DATABASE_NAME]
instance = Instance.from_db(database)

# ---------------------------
# Document model
# ---------------------------
@instance.register
class Data(Document):
    id = fields.StrField(attribute="_id", required=True)
    use = fields.StrField(required=True, default="forward", marshmallow_default="forward")
    caption = fields.StrField(required=True, default="No Caption", marshmallow_default="No Caption")

    class Meta:
        collection_name = COLLECTION_NAME

# ---------------------------
# Save a media entry in DB
# ---------------------------
async def save_data(file_id: str, caption: str):
    try:
        data = Data(id=file_id, caption=caption)
        await data.commit()
    except ValidationError as e:
        logger.exception(f"Validation error while saving: {e}")
    except DuplicateKeyError:
        logger.warning(f"File {file_id} already exists in DB")
    else:
        logger.info(f"Message {file_id} saved in DB")

# ---------------------------
# Fetch the next message(s) to forward
# ---------------------------
async def get_search_results(limit: int = 1):
    cursor = Data.find({'use': "forward"}).sort('$natural', 1).limit(limit)
    messages = await cursor.to_list(length=limit)
    return messages

# ---------------------------
# Utility: Count all messages
# ---------------------------
async def count_messages():
    return await Data.collection.count_documents({})
