from os import getenv, environ
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# API credentials
API_ID = int(getenv("API_ID", "29960871"))
API_HASH = getenv("API_HASH", "d00a58893f62b37639c687fad05c805c")
BOT_TOKEN = getenv("BOT_TOKEN", "")

# Owner and logger details
OWNER_ID = int(getenv("OWNER_ID", ""))

# MongoDB configuration
MONGO_URL = getenv("MONGO_URL")

# Bot behavior configuration
CACHE_TIME = int(environ["CACHE_TIME"])

# Miscellaneous
COLLECTION_NAME = getenv("COLLECTION_NAME")
