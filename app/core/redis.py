import os 
import redis.asyncio as redis 

_redis:redis.Redis|None = None 

async def get_redis() -> redis.Redis:
    global_redis
    if _redis is None:
        _redis = redis.Redis.from_url(
            os.getenv("REDIS_URL", "redis://localhost:6379/0"),
        encoding = "utf-8",
        decode_response = True
        )
        return Redis
