import httpx
from typing import Any, Dict, List, Optional
from app.core.config import settings
from app.external.rate_limiter import get_rate_limiter

POLYGON_BASE = "https://api.polygon.io"


async def _get(path: str, params: Optional[Dict] = None) -> Optional[Dict]:
    if not settings.POLYGON_API_KEY or settings.POLYGON_API_KEY == "placeholder_polygon_api_key":
        return None
    limiter = get_rate_limiter("polygon")
    await limiter.wait()
    async with httpx.AsyncClient() as client:
        try:
            resp = await client.get(
                f"{POLYGON_BASE}{path}",
                params={**(params or {}), "apiKey": settings.POLYGON_API_KEY},
                timeout=10,
            )
            resp.raise_for_status()
            return resp.json()
        except Exception:
            return None


async def get_quote(symbol: str) -> Optional[Dict[str, Any]]:
    data = await _get(f"/v2/snapshot/locale/us/markets/stocks/tickers/{symbol}")
    if data and "ticker" in data:
        t = data["ticker"]
        return {
            "symbol": symbol.upper(),
            "price": t.get("day", {}).get("c"),
            "change": t.get("todaysChange"),
            "change_pct": t.get("todaysChangePerc"),
            "volume": t.get("day", {}).get("v"),
            "previous_close": t.get("prevDay", {}).get("c"),
            "high": t.get("day", {}).get("h"),
            "low": t.get("day", {}).get("l"),
        }
    return None


async def get_history(symbol: str, timespan: str = "day", multiplier: int = 1, from_date: str = "", to_date: str = "") -> List[Dict]:
    data = await _get(f"/v2/aggs/ticker/{symbol}/range/{multiplier}/{timespan}/{from_date}/{to_date}")
    if data and "results" in data:
        return [
            {
                "date": r.get("t"),
                "open": r.get("o"),
                "high": r.get("h"),
                "low": r.get("l"),
                "close": r.get("c"),
                "volume": r.get("v"),
            }
            for r in data["results"]
        ]
    return []
