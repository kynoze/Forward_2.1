from umongo.frameworks.motor_asyncio import MotorAsyncIOInstance
from motor.motor_asyncio import AsyncIOMotorClient
import config

# Asynchronous Database Connection
ForwardDB = AsyncIOMotorClient(config.MONGO_URL)

# Database
db = ForwardDB["ForwardDB"]
instance = MotorAsyncIOInstance(db)

