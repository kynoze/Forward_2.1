from os import getenv, environ
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# API credentials
API_ID = int(getenv("API_ID", "29960871"))
API_HASH = getenv("API_HASH", "d00a58893f62b37639c687fad05c805c")
BOT_TOKEN = "5873965762:AAEiw1PiXvIo-DnM9-nEu8ZiPKIWxNH11Ng"
#getenv("BOT_TOKEN", "6658841062:AAGiWmocc3T3trwvhDm6jxheh1X0Y-hcwHE")

# Owner and logger details
OWNER_ID = int(getenv("OWNER_ID", "5326801541"))

# MongoDB configuration
MONGO_URL = getenv("MONGO_URL", "mongodb+srv://autopost763:OMnkmZFLXUu0lgnQ@cluster0.wcxqdzt.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0")

# Bot behavior configuration
CACHE_TIME = 300 #int(environ["CACHE_TIME"])

# Miscellaneous
COLLECTION_NAME = getenv("COLLECTION_NAME", "forward2025")
