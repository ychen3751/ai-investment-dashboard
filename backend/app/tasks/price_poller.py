import json
from datetime import datetime, timezone

from app.external import yahoo_finance
from app.services.market_data_service import get_tracked_symbols
from app.websocket.manager import manager
from app.core.cache import get_redis


async def poll_prices():
    """Poll current prices for tracked symbols and broadcast via WebSocket."""
    symbols = await get_tracked_symbols()
    if not symbols:
        return

    redis = await get_redis()
    for symbol in symbols:
        try:
            quote = await yahoo_finance.get_quote(symbol)
            if not quote:
                continue

            tick = {
                "symbol": quote["symbol"],
                "price": quote["price"],
                "change": quote.get("change"),
                "change_pct": quote.get("change_pct"),
                "volume": quote.get("volume"),
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }

            await redis.setex(f"price:{symbol}", 60, json.dumps(tick, default=str))
            await manager.broadcast(symbol, tick)
        except Exception:
            continue
