import redis.asyncio as redis
from app.core.config import settings

class RedisClient:
    client: redis.Redis = None

redis_client = RedisClient()

async def get_redis() -> redis.Redis:
    return redis_client.client

async def connect_to_redis():
    print("Connecting to Redis...")
    redis_client.client = redis.Redis(
        host=settings.REDIS_HOST,
        port=settings.REDIS_PORT,
        decode_responses=True
    )
    print("Redis connected!")

async def close_redis_connection():
    print("Closing Redis connection...")
    await redis_client.client.close()
    print("Redis connection closed.")