import re
from pymongo.errors import DuplicateKeyError, PyMongoError
from umongo import Document, fields
from marshmallow.exceptions import ValidationError
from database import db, instance
from config import COLLECTION_NAME
import logging
from typing import Any, Optional
from helper.clean_file_name import clean_file_name

logger = logging.getLogger(__name__)

@instance.register
class Media(Document):
    file_unique_id = fields.StrField(attribute='_id', required=True)  # primary key for duplicate check
    file_id = fields.StrField(allow_none=True)  # optional Telegram file_id
    caption = fields.StrField(allow_none=True)  # original caption or file_name if caption missing
    use = fields.StrField(required=True)

    class Meta:
        collection_name = COLLECTION_NAME

async def is_file_already_saved(file_unique_id: str, col) -> bool:
    try:
        found = await col.find_one({"_id": file_unique_id})
        return found is not None
    except PyMongoError:
        logger.exception("DB error while checking duplicates in %s", getattr(col, "name", "<collection>"))
        return False

async def save_file(media: Any, col) -> str:
    file_unique_id = getattr(media, "file_unique_id", None)
    file_id = getattr(media, "file_id", None)
    if not file_unique_id:
        logger.error("save_file: media has no file_unique_id; media=%s", type(media))
        return 'err'

    if await is_file_already_saved(file_unique_id, col):
        return 'dup'

    org_caption = getattr(media, "caption", None)  # original caption
    if not org_caption:
        org_caption = getattr(media, "file_name", None)  # fallback to file_name if caption missing

    if clean_name:
        org_caption = clean_file_name(org_caption)
        
    file = Media(
        file_unique_id=file_unique_id,
        file_id=file_id,
        caption=org_caption,
        use='forward',
    )
    try:
        await file.commit()
        return 'suc'
    except DuplicateKeyError:
        logger.warning("DuplicateKeyError while inserting %s", file_unique_id)
        return 'dup'
    except PyMongoError as e:
        logger.exception("PyMongoError while inserting %s: %s", file_unique_id, e)
        return 'err'
    except Exception as e:
        logger.exception("Unexpected error while inserting %s: %s", file_unique_id, e)
        return 'err'

async def get_search_results(limit: int = 1):
    cursor = Media.find({'use': "forward"})
    cursor.sort('$natural', 1)
    cursor.skip(0).limit(limit)
    messages = await cursor.to_list(length=limit)
    return messages
