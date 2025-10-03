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


async def search_files(query, max_results=8, offset=0, lang=None):  
    query = query.strip()  
    raw_pattern = (
        r'(\b|[\.\+\-_])' + query + r'(\b|[\.\+\-_])'
        if ' ' not in query else
        query.replace(' ', r'.*[\s\.\+\-_]')
    )

    try:  
        regex = re.compile(raw_pattern, flags=re.IGNORECASE)  
    except Exception:  
        regex = query  

    filter_criteria = {'file_name': regex}  
    cursor = Media.find(filter_criteria).sort('$natural', -1)  

    if lang:  
        lang_files = [
            file async for file in cursor
            if "file_name" in file and lang in file["file_name"].lower()
        ]
        return (
            lang_files[offset:][:max_results],
            offset + max_results if offset + max_results < len(lang_files) else '',
            len(lang_files)
        )

    files = await cursor.skip(offset).limit(max_results).to_list(length=max_results)  
    total_results = await Media.count_documents(filter_criteria)  
    next_offset = offset + max_results if offset + max_results < total_results else ''  

    return files, next_offset, total_results


async def get_bad_files(query, file_type=None):
    query = query.strip()
    raw_pattern = (
        r'(\b|[\.\+\-_])' + query + r'(\b|[\.\+\-_])'
        if ' ' not in query else
        query.replace(' ', r'.*[\s\.\+\-_]')
    )

    try:
        regex = re.compile(raw_pattern, flags=re.IGNORECASE)
    except Exception:
        return []

    filter_criteria = {'file_name': regex}
    if file_type:
        filter_criteria['file_type'] = file_type

    files = await Media.find(filter_criteria).sort('$natural', -1).to_list(length=None)
    return files, len(files)


async def get_file_details(file_id):
    try:
        return await Media.find({'file_id': file_id}).to_list(length=1)
    except Exception:
        return []


def encode_file_id(s: bytes) -> str:
    r, n = b"", 0
    for i in s + bytes([22, 4]):
        if i == 0:
            n += 1
        else:
            if n:
                r += b"\x00" + bytes([n])
                n = 0
            r += bytes([i])
    return base64.urlsafe_b64encode(r).decode().rstrip("=")


def encode_file_ref(file_ref: bytes) -> str:
    return base64.urlsafe_b64encode(file_ref).decode().rstrip("=")


def unpack_new_file_id(new_file_id):
    try:
        decoded = FileId.decode(new_file_id)
        return (
            encode_file_id(pack("<iiqq", int(decoded.file_type), decoded.dc_id, decoded.media_id, decoded.access_hash)),
            encode_file_ref(decoded.file_reference)
        )
    except Exception:
        return None, None


def formate_file_name(file_name):
    return ' '.join(
        filter(
            lambda x: not x.startswith('[') and not x.startswith('@') and not x.startswith('www.'),
            file_name.split()
        )
      )
