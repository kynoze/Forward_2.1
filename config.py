from os import getenv, environ
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

API_ID = int(getenv("API_ID", ""))
API_HASH = getenv("API_HASH", "")
TG_BOT_TOKEN = getenv("TG_BOT_TOKEN", "")
OWNER_ID = set(int(x) for x in getenv("OWNER_ID", "").split())
MONGO_URL = getenv("MONGO_URL", "")
CACHE_TIME = 300 #int(environ["CACHE_TIME"])
COLLECTION_NAME = getenv("COLLECTION_NAME", "forward2025")
