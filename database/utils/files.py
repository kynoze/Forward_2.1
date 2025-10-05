import logging
import re
from typing import Optional, Any, Dict
from pymongo.errors import DuplicateKeyError, PyMongoError
from umongo import Document, fields
from database import db, instance
from config import COLLECTION_NAME

logger = logging.getLogger(__name__)

@instance.register
class Media(Document):
    # maps 'file_id' field to MongoDB document _id
    file_id = fields.StrField(attribute='_id', required=True)
    file_name = fields.StrField(allow_none=True)        # add file_name to schema
    caption = fields.StrField(allow_none=True)
    use = fields.StrField(required=True)

    class Meta:
        collection_name = COLLECTION_NAME


def _normalize_text(s: Optional[str]) -> Optional[str]:
    """Normalize strings for comparisons. Return None for falsy values."""
    if not s:
        return None
    s = s.strip()
    if not s:
        return None
    # collapse whitespace and lowercase for easier duplicate detection
    s = re.sub(r'\s+', ' ', s)
    return s.lower()


async def is_file_already_saved(file_id: str,
                                file_name: Optional[str],
                                caption: Optional[str],
                                col, sec_col) -> bool:
    """
    Check if the file is already saved in either collection (match _id/file_id/file_name/caption).
    Uses a single $or query per collection for efficiency.
    """
    file_name_norm = _normalize_text(file_name)
    caption_norm = _normalize_text(caption)

    or_clauses = [
        {"_id": file_id},         # matches umongo-mapped primary key
        {"file_id": file_id},     # in case documents store file_id field explicitly
    ]
    if file_name_norm:
        or_clauses.append({"file_name": file_name_norm})
    if caption_norm:
        or_clauses.append({"caption": caption_norm})

    query = {"$or": or_clauses}

    for collection in (col, sec_col):
        found = await collection.find_one(query)
        if found:
            logger.info("Duplicate found %s in collection %s", query, getattr(collection, "name", "<collection>"))
            return True
    return False


async def save_file(media: Any, col, sec_col) -> str:
    """
    Save a file document into `col` (Motor collection). Returns:
      - 'dup' on duplicate,
      - 'suc' on success,
      - 'err' on other errors.
    """
    file_id = getattr(media, "file_id", None)
    if not file_id:
        logger.error("No file_id present on media object")
        return 'err'

    file_name = getattr(media, "file_name", None)
    # if caption is an object with .html (pyrogram), handle safely
    raw_caption = None
    if getattr(media, "caption", None):
        raw_caption = getattr(media.caption, "html", None) or str(media.caption)

    # normalize fields before storing/searching
    file_name_norm = _normalize_text(file_name)
    caption_norm = _normalize_text(raw_caption)

    if await is_file_already_saved(file_id, file_name_norm, caption_norm, col, sec_col):
        logger.info("Duplicate file (id=%s). Skipping save.", file_id)
        return 'dup'

    file_data: Dict[str, Any] = {
        '_id': file_id,  # store as _id so it matches umongo mapping
        'file_id': file_id,  # optional duplicate field for compatibility
        'file_name': file_name_norm,
        'caption': caption_norm,
        # add other fields as needed, e.g. 'use', 'date', etc.
    }

    try:
        await col.insert_one(file_data)
        logger.info("Inserted file %s into %s", file_id, getattr(col, "name", "<collection>"))
        return 'suc'
    except DuplicateKeyError:
        # In case a race condition occurred or index exists
        logger.warning("DuplicateKeyError while inserting %s", file_id)
        return 'dup'
    except PyMongoError as e:
        logger.exception("PyMongoError while inserting %s: %s", file_id, e)
        return 'err'
    except Exception as e:
        logger.exception("Unexpected error while inserting %s: %s", file_id, e)
        return 'err'

    
async def get_search_results():
    filter = {'use': "forward"}
    cursor = Media.find(filter)
    cursor.sort('$natural', 1)
    cursor.skip(0).limit(1)
    messages = await cursor.to_list(length=1)
    return messages
