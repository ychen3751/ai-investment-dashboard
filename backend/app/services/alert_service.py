from typing import Any, Dict
from app.services import market_data_service


async def check_price_alert(symbol: str, condition: Dict[str, Any]) -> bool:
    """Check if price crossed the threshold."""
    quote = await market_data_service.get_quote(symbol)
    if not quote or not quote.get("price"):
        return False
    price = float(quote["price"])
    target = float(condition.get("target", 0))
    if condition.get("direction") == "above":
        return price >= target
    return price <= target


async def check_volume_alert(symbol: str, condition: Dict[str, Any]) -> bool:
    """Check if volume surged above multiplier * average volume."""
    quote = await market_data_service.get_quote(symbol)
    if not quote or not quote.get("volume") or not quote.get("avg_volume"):
        return False
    volume = int(quote["volume"])
    avg_volume = int(quote["avg_volume"])
    multiplier = float(condition.get("multiplier", 2.0))
    return volume >= avg_volume * multiplier
