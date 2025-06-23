from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from app.core.config import settings

class DataBase:
    client: AsyncIOMotorClient = None
    db: AsyncIOMotorDatabase = None

database = DataBase()

async def get_db() -> AsyncIOMotorDatabase:
    return database.db

async def connect_to_mongo():
    print("Connecting to MongoDB...")
    database.client = AsyncIOMotorClient(settings.MONGO_DETAILS)
    database.db = database.client[settings.DB_NAME]

    await database.db.agents.create_index([("location", "2dsphere")])
    print("MongoDB connected!")

async def close_mongo_connection():
    print("Closing MongoDB connection...")
    database.client.close()
    print("MongoDB connection closed.")