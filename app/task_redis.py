import redis.asyncio as aioredis
from app.config import REDIS_HOST


async def get_redis() -> aioredis.Redis:
    return aioredis.from_url(
        f"redis://{REDIS_HOST}:6379", 
        decode_responses=True,
        )