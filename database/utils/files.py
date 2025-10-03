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
class Media(Document):
    file_id = fields.StrField(attribute='_id', required=True)
    file_ref = fields.StrField(allow_none=True)
    file_name = fields.StrField(required=True)
    file_size = fields.IntField(required=True)
    mime_type = fields.StrField(allow_none=True)
    caption = fields.StrField(allow_none=True)
    file_type = fields.StrField(allow_none=True)

    class Meta:
        indexes = ('$file_name',)
        collection_name = COLLECTION_NAME


async def save_file(media):
    file_id, file_ref = unpack_new_file_id(media.file_id)
    file_name = re.sub(r"(_|\-|\.|\+)", " ", str(media.file_name))

    try:
        file = Media(
            use='forward'
            file_id=file_id,
            file_ref=file_ref,
            file_name=file_name,
            file_size=media.file_size,
            mime_type=media.mime_type,
            caption=media.caption.html if media.caption else None,
            file_type=media.mime_type.split('/')[0] if media.mime_type else None
        )
        await file.commit()
        return 'suc'

    except ValidationError:
        return 'err'

    except DuplicateKeyError:
        return 'dup'

    except Exception:
        return 'err'

async def get_search_results():
    filter = {'use': 'forward'}
    cursor = Data.find(filter)
    cursor.sort('$natural', 1)
    cursor.skip(0).limit(1)
    Messages = await cursor.to_list(length=1)
    return Messages
