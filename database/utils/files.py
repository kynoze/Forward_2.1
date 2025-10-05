import re
from pymongo.errors import DuplicateKeyError
from umongo import Document, fields
from marshmallow.exceptions import ValidationError
from database import db, instance
from config import COLLECTION_NAME


@instance.register
class Media(Document):
    file_id = fields.StrField(attribute='_id', required=True)
    caption = fields.StrField(allow_none=True)
    use = fields.StrField(required=True)

    class Meta:
        collection_name = COLLECTION_NAME


def _normalize_text(s: Optional[str]) -> Optional[str]:
    """Normalize strings for comparisons. Return None for falsy values."""
    if not s:
        return None
    s = str(s).strip()
    if not s:
        return None
    # collapse whitespace and lowercase for easier duplicate detection
    s = re.sub(r'\s+', ' ', s)
    return s.lower()


async def is_file_already_saved(file_id: str,
                                file_name: Optional[str],
                                caption: Optional[str],
                                col) -> bool:
    """
    Check if the file is already saved in the collection (match _id/file_name/caption).
    Uses a single $or query for efficiency.
    """
    file_name_norm = _normalize_text(file_name)
    caption_norm = _normalize_text(caption)

    or_clauses = [{"file_id": file_id}]
    if file_name_norm:
        or_clauses.append({"file_name": file_name_norm})
    if caption_norm:
        or_clauses.append({"caption": caption_norm})

    query = {"$or": or_clauses}

    try:
        found = await col.find_one(query)
        if found:
            logger.info("Duplicate found %s in %s", query, getattr(col, "name", "<collection>"))
            return True
    except PyMongoError:
        logger.exception("DB error while checking duplicates in %s", getattr(col, "name", "<collection>"))
    return False


async def save_file(media: Any, col) -> str:
    file_id = getattr(media, "file_id", None) or getattr(media, "file_unique_id", None)
    if not file_id:
        logger.error("save_file: media has no file_id; media=%s", type(media))
        return 'err'
    file_name_raw = getattr(media, "file_name", None) or getattr(media, "file_path", None)
    file_name_norm = _normalize_text(file_name_raw)

    raw_caption = None
    cap_obj = getattr(media, "caption", None)
    if cap_obj:
        html = getattr(cap_obj, "html", None)
        text = getattr(cap_obj, "text", None)
        if html:
            raw_caption = html
        elif text:
            raw_caption = text
        else:
            raw_caption = str(cap_obj)
    caption_norm = _normalize_text(raw_caption)

    # Duplicate check
    try:
        if await is_file_already_saved(file_id, file_name_norm, caption_norm, col):
            return 'dup'
    except Exception:
        logger.exception("Duplicate check failed; proceeding to insert for file_id=%s", file_id)

    # Prepare document (do NOT store 'file_id'; _id handles it)
    file = Media(
        'file_id': file_id,
        'file_name': file_name_norm,
        'caption': caption_norm,
        'use': 'forward',
    )
    try:
        await file.commit()
        #logger.info("Inserted file %s into %s", file_id, getattr(col, "name", "<collection>"))
        return 'suc'
    except DuplicateKeyError:
        logger.warning("DuplicateKeyError while inserting %s", file_id)
        return 'dup'
    except PyMongoError as e:
        logger.exception("PyMongoError while inserting %s: %s", file_id, e)
        return 'err'
    except Exception as e:
        logger.exception("Unexpected error while inserting %s: %s", file_id, e)
        return 'err'


async def get_search_results(limit: int = 1):
    """
    Fetch messages filtered by 'use': 'forward'.
    Returns a list of Media objects.
    """
    cursor = Media.find({'use': "forward"})
    cursor.sort('$natural', 1)
    cursor.skip(0).limit(limit)
    messages = await cursor.to_list(length=limit)
    return messages
