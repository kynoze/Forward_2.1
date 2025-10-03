from os import getenv, environ
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# API credentials
API_ID = int(getenv("API_ID", ""))
API_HASH = getenv("API_HASH", "")
BOT_TOKEN = getenv("BOT_TOKEN", "")

# Owner and logger details
OWNER_ID = int(getenv("OWNER_ID", ""))

# MongoDB configuration
MONGO_URL = getenv("MONGO_URL")

# Bot behavior configuration
CACHE_TIME = int(environ["CACHE_TIME"])

# Miscellaneous
COLLECTION_NAME = getenv("COLLECTION_NAME")
