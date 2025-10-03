import logging
from pymongo.errors import DuplicateKeyError
from umongo import Instance, Document, fields
from motor.motor_asyncio import AsyncIOMotorClient
from marshmallow import ValidationError
from config import Config

# Logger setup
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# Database configuration
DATABASE_URI = Config.DATABASE_URI
DATABASE_NAME = "forward_media"
COLLECTION_NAME = "media-collection"

# Async MongoDB client
client = AsyncIOMotorClient(DATABASE_URI)
database = client[DATABASE_NAME]
instance = Instance.from_db(database)

# Document model for media messages
@instance.register
class Data(Document):
    id = fields.StrField(attribute='_id', required=True, default=None)
    use = fields.StrField(required=True, default="forward")
    caption = fields.StrField(required=True, default="No Caption", marshmallow_default="No Caption")

    class Meta:
        collection_name = COLLECTION_NAME

# Save a media entry to the database
async def save_data(file_id: str, caption: str):
    try:
        data = Data(
            id=file_id,
            use="forward",
            caption=caption or "No Caption"
        )
        await data.commit()
    except ValidationError as e:
        logger.exception(f"Validation error while saving: {e}")
    except DuplicateKeyError:
        logger.warning(f"File {file_id} already exists in DB")
    else:
        logger.info(f"Message {file_id} saved in DB")

# Fetch the next message(s) to forward
async def get_search_results(limit: int = 1):
    """
    Fetch messages from DB with 'use' == 'forward'.
    Default fetch: 1 message.
    """
    cursor = Data.find({'use': "forward"}).sort('$natural', 1).limit(limit)
    messages = await cursor.to_list(length=limit)
    return messages
