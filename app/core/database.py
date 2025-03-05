from motor.motor_asyncio import AsyncIOMotorClient
from app.core.config import settings

client = AsyncIOMotorClient(settings.MONGODB_URI)
db = client.get_default_database()

async def get_db():
    yield db

# Create geospatial index for agents and orders
async def init_db():
    await db.agents.create_index([("location", "2dsphere")])
    await db.orders.create_index([("order_location", "2dsphere")])