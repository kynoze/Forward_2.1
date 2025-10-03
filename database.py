import logging
from pymongo.errors import DuplicateKeyError
from umongo import Instance, Document, fields
from motor.motor_asyncio import AsyncIOMotorClient
from marshmallow import ValidationError
from config import Config

# Logger setup
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# Database config
DATABASE_URI = Config.DATABASE_URI
DATABASE_NAME = "forward_media"
COLLECTION_NAME = "media-collection"

# Async MongoDB client
client = AsyncIOMotorClient(DATABASE_URI)
database = client[DATABASE_NAME]
instance = Instance.from_db(database)

# Document model
@instance.register
class Data(Document):
    id = fields.StrField(attribute='_id', required=True)
    use = fields.StrField(required=True)
    caption = fields.StrField(required=True)

    class Meta:
        collection_name = COLLECTION_NAME

# Save a media entry in DB
async def save_data(id: str, caption: str):
    try:
        data = Data(
            id=id,
            use="forward",
            caption=caption
        )
        await data.commit()
    except ValidationError as e:
        logger.exception(f"Validation error while saving: {e}")
    except DuplicateKeyError:
        logger.warning("Already saved in Database")
    else:
        logger.info("Message saved in DB")

# Fetch the next message to forward
async def get_search_results():
    cursor = Data.find({'use': "forward"}).sort('$natural', 1).limit(1)
    messages = await cursor.to_list(length=1)
    return messages
