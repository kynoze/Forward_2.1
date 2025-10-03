import logging
from pymongo.errors import DuplicateKeyError
from umongo import Instance, Document, fields
from motor.motor_asyncio import AsyncIOMotorClient
from marshmallow import ValidationError
from config import Config

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# MongoDB setup
client = AsyncIOMotorClient(Config.DATABASE_URI)
database = client["forward_media"]
instance = Instance.from_db(database)

@instance.register
class Data(Document):
    id = fields.StrField(attribute="_id", required=True)
    use = fields.StrField(required=True)
    caption = fields.StrField(required=True)

    class Meta:
        collection_name = "media-collection"

    def __init__(self, **kwargs):
        if "use" not in kwargs or not kwargs["use"]:
            kwargs["use"] = "forward"
        if "caption" not in kwargs or not kwargs["caption"]:
            kwargs["caption"] = "No Caption"
        super().__init__(**kwargs)

# Save message in DB
async def save_data(file_id: str, caption: str):
    try:
        data = Data(id=file_id, caption=caption)
        await data.commit()
    except ValidationError as e:
        logger.exception(f"Validation error: {e}")
    except DuplicateKeyError:
        logger.warning(f"File {file_id} already exists in DB")
    else:
        logger.info(f"Message {file_id} saved in DB")

# Get next messages to forward
async def get_search_results(limit: int = 1):
    cursor = Data.find({"use": "forward"}).sort("$natural", 1).limit(limit)
    messages = await cursor.to_list(length=limit)
    return messages
