import json
from functools import wraps
from typing import Any, Callable, Optional
import redis.asyncio as aioredis

from app.core.config import settings

_redis: Optional[aioredis.Redis] = None


async def get_redis() -> Optional[aioredis.Redis]:
    global _redis
    if _redis is not None:
        return _redis
    if not settings.REDIS_URL:
        return None
    try:
        _redis = aioredis.from_url(
            settings.REDIS_URL,
            encoding="utf-8",
            decode_responses=True,
        )
    except Exception:
        return None
    return _redis


class _NullRedis:
    """Stand-in when Redis is unavailable — all operations no-op."""
    async def get(self, *a, **kw): return None
    async def setex(self, *a, **kw): pass
    async def smembers(self, *a, **kw): return set()
    async def sadd(self, *a, **kw): pass
    async def publish(self, *a, **kw): pass


_null_redis = _NullRedis()


async def get_redis_safe() -> Any:
    """Like get_redis() but never returns None (returns a no-op stub instead).

    Callers that want resilience should use this; callers that need real Redis
    should use get_redis() and handle None.
    """
    r = await get_redis()
    return r if r is not None else _null_redis


async def close_redis():
    global _redis
    if _redis:
        try:
            await _redis.close()
        except Exception:
            pass
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
