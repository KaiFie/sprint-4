from typing import Optional

from aioredis import Redis


redis: Optional[Redis] = None
cache: Optional[Redis] = None


async def get_redis() -> Redis:
    """
    Helper to inject dependency of Redis client.

    Returns:
        Redis instance

    """

    return redis
