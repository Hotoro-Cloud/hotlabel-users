import os
from typing import Optional
from redis.asyncio import ConnectionPool, Redis
from app.core.config import settings

_redis_pool: Optional[ConnectionPool] = None

async def get_redis_pool() -> ConnectionPool:
    global _redis_pool
    if _redis_pool is None:
        _redis_pool = ConnectionPool.from_url(
            settings.REDIS_URL,
            decode_responses=True,
            max_connections=10
        )
    return _redis_pool

async def get_redis() -> Redis:
    pool = await get_redis_pool()
    return Redis(connection_pool=pool) 