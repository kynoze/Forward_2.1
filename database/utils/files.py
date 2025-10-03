import re
import base64
from struct import pack
from pymongo.errors import DuplicateKeyError
from umongo import Document, fields
from marshmallow.exceptions import ValidationError
from pyrogram.file_id import FileId
from database import db, instance
from config import COLLECTION_NAME


@instance.register
class Data(Document):
    id = fields.StrField(attribute='_id')
    use = fields.StrField(required=True)
    caption = fields.StrField(allow_none=True)
    file_type = fields.StrField(required=True)
    channel_id = fields.StrField(allow_none=True)
    message_id = fields.StrField(allow_none=True)
    class Meta:
        collection_name = COLLECTION_NAME

async def save_data(id, caption, file_type, channel_id, message_id):
    try:
        data = Data(
            id=id,
            use = "forward",
            caption=caption,
            file_type=file_type,
            channel_id=channel_id,
            message_id=message_id
        )
    except ValidationError:
        logger.exception('Error occurred while saving file in database')
    else:
        try:
            await data.commit()
        except DuplicateKeyError:
            logger.warning("Already saved in Database")
        else:
            logger.info("Messsage saved in DB")


async def get_search_results():
    filter = {'use': "forward"}
    cursor = Data.find(filter)
    cursor.sort('$natural', 1)
    cursor.skip(0).limit(1)
    Messages = await cursor.to_list(length=1)
    return Messages
