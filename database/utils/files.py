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
    file_name = fields.StrField(required=True)
    caption = fields.StrField(allow_none=True)
    
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
            file_name=file_name,
            caption=media.caption.html if media.caption else None,
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
