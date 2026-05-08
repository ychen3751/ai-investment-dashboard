from typing import Any, Dict, List, Optional
from app.external import yahoo_finance, polygon
from app.core.cache import get_redis


async def get_quote(symbol: str) -> Optional[Dict[str, Any]]:
    redis = await get_redis()
    cache_key = f"quote:{symbol.upper()}"
    cached = await redis.get(cache_key)
    if cached:
        import json
        return json.loads(cached)

    result = await yahoo_finance.get_quote(symbol)
    if not result:
        result = await polygon.get_quote(symbol)

    if result:
        import json
        await redis.setex(cache_key, 30, json.dumps(result, default=str))
    return result


async def get_history(symbol: str, interval: str = "1d", range_str: str = "1mo") -> List[Dict[str, Any]]:
    redis = await get_redis()
    cache_key = f"hist:{symbol.upper()}:{interval}:{range_str}"
    cached = await redis.get(cache_key)
    if cached:
        import json
        return json.loads(cached)

    result = await yahoo_finance.get_history(symbol, interval, range_str)
    if result:
        import json
        await redis.setex(cache_key, 300, json.dumps(result, default=str))
    return result


async def get_info(symbol: str) -> Dict[str, Any]:
    redis = await get_redis()
    cache_key = f"info:{symbol.upper()}"
    cached = await redis.get(cache_key)
    if cached:
        import json
        return json.loads(cached)

    result = await yahoo_finance.get_info(symbol)
    if result:
        import json
        await redis.setex(cache_key, 3600, json.dumps(result, default=str))
    return result


async def search_symbols(query: str) -> List[Dict[str, str]]:
    if len(query) < 1:
        return []
    return await yahoo_finance.search_symbols(query)


async def get_tracked_symbols() -> List[str]:
    redis = await get_redis()
    symbols = await redis.smembers("tracked_symbols")
    return list(symbols) if symbols else []


async def add_tracked_symbol(symbol: str):
    redis = await get_redis()
    await redis.sadd("tracked_symbols", symbol.upper())
