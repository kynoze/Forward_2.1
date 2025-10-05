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

def is_file_already_saved(file_id, file_name, caption, col, sec_col):
    """Check if the file is already saved in either collection (by id, name, or caption)."""
    queries = [
        {'file_id': file_id},
        {'file_name': file_name},
        {'caption': caption},
    ]

    for collection in [col, sec_col]:
        for query in queries:
            if collection.find_one(query):
                print(f"Duplicate found ({query}) in {collection.name}. Skipping save.")
                return True
    return False

# Usage in your save function
async def save_file(media, col, sec_col):
    file_id = media.file_id
    file_name = getattr(media, "file_name", "Unnamed File")
    caption = media.caption.html if media.caption else "No Caption"

    if is_file_already_saved(file_id, file_name, caption, col, sec_col):
        print("Duplicate file. Skipping save.")
        return 'dup'

    try:
        file_data = {
            'file_id': file_id,
            'file_name': file_name,
            'caption': caption,
            # add other fields as needed
        }
        await col.insert_one(file_data)
        return 'suc'
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
