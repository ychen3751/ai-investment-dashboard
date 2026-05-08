import json
from functools import wraps
from typing import Any, Callable, Optional
import redis.asyncio as aioredis

from app.core.config import settings

_redis: Optional[aioredis.Redis] = None


async def get_redis() -> aioredis.Redis:
    global _redis
    if _redis is None:
        _redis = aioredis.from_url(
            settings.REDIS_URL,
            encoding="utf-8",
            decode_responses=True,
        )
    return _redis


async def close_redis():
    global _redis
    if _redis:
        await _redis.close()
        _redis = None


def cached(ttl: int = 300):
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            try:
                redis = await get_redis()
                key_parts = [func.__name__]
                key_parts.extend(str(a) for a in args)
                key_parts.extend(f"{k}:{v}" for k, v in sorted(kwargs.items()))
                cache_key = ":".join(key_parts)

                cached_value = await redis.get(cache_key)
                if cached_value is not None:
                    return json.loads(cached_value)

                result = await func(*args, **kwargs)
                await redis.setex(cache_key, ttl, json.dumps(result, default=str))
                return result
            except Exception:
                return await func(*args, **kwargs)

        return wrapper

    return decorator
