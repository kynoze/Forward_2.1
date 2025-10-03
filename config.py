from os import getenv, environ
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

API_ID = int(getenv("API_ID", "29960871"))
API_HASH = getenv("API_HASH", "d00a58893f62b37639c687fad05c805c")
TG_BOT_TOKEN = getenv("TG_BOT_TOKEN", "")
OWNER_ID = int(getenv("OWNER_ID", "5326801541"))
MONGO_URL = getenv("MONGO_URL", "mongodb+srv://autopost763:OMnkmZFLXUu0lgnQ@cluster0.wcxqdzt.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0")
CACHE_TIME = 300 #int(environ["CACHE_TIME"])
COLLECTION_NAME = getenv("COLLECTION_NAME", "forward2025")
