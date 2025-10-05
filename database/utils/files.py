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

# ✅ Save file to MongoDB, skip if duplicate
async def save_file(media):
    file_name = getattr(media, "file_name", "Unnamed File")
    caption = media.caption.html if media.caption else re.sub(r"[_\-\.]+", " ", file_name)

    # Check for duplicate before saving
    existing = await Media.find_one({'_id': media.file_id})
    if existing:
        return 'dup'  # Duplicate found, skip saving

    try:
        file = Media(
            use='forward',
            file_id=media.file_id,
            caption=caption
        )
        await file.commit()
        return 'suc'

    except ValidationError:
        return 'err'

    except Exception as e:
        print(f"Error saving file: {e}")
        return 'err'

    
async def get_search_results():
    filter = {'use': "forward"}
    cursor = Media.find(filter)
    cursor.sort('$natural', 1)
    cursor.skip(0).limit(1)
    messages = await cursor.to_list(length=1)
    return messages
