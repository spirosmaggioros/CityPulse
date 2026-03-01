import os

import redis.asyncio as aioredis

REDIS_HOST = os.getenv("REDIS_HOST", "redis")
REDIS_PORT = int(os.getenv("REDIS_PORT", "6379"))

_redis: aioredis.Redis | None = None


def get_redis() -> aioredis.Redis:
    global _redis
    if _redis is None:
        _redis = aioredis.Redis(
            host=REDIS_HOST,
            port=REDIS_PORT,
            db=0,
            decode_responses=True,
            socket_connect_timeout=10,
            socket_keepalive=True,
            health_check_interval=30,
        )
    return _redis


async def check_redis_connection() -> None:
    r = get_redis()
    await r.ping()


async def close_redis() -> None:
    global _redis
    if _redis is not None:
        await _redis.aclose()
        _redis = None
