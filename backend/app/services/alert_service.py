"""Alert evaluation engine — checks conditions against live market data."""
from typing import Any, Dict
from app.services import market_data_service
from app.services.technical_service import rsi as compute_rsi


async def check_price_alert(symbol: str, condition: Dict[str, Any]) -> bool:
    """Trigger when price crosses a target threshold."""
    quote = await market_data_service.get_quote(symbol)
    if not quote or quote.get("price") is None:
        return False
    price = float(quote["price"])
    target = float(condition.get("target", 0))
    direction = condition.get("direction", "above")
    return price >= target if direction == "above" else price <= target


async def check_daily_pct_alert(symbol: str, condition: Dict[str, Any]) -> bool:
    """Trigger when daily percent change exceeds a threshold."""
    quote = await market_data_service.get_quote(symbol)
    if not quote or quote.get("change_pct") is None:
        return False
    change_pct = float(quote["change_pct"])
    threshold = float(condition.get("threshold", 0))
    direction = condition.get("direction", "above")
    return change_pct >= threshold if direction == "above" else change_pct <= -threshold


async def check_volume_alert(symbol: str, condition: Dict[str, Any]) -> bool:
    """Trigger when volume surges above multiplier × average volume."""
    quote = await market_data_service.get_quote(symbol)
    if not quote or quote.get("volume") is None or quote.get("avg_volume") is None:
        return False
    volume = int(quote["volume"])
    avg_volume = int(quote["avg_volume"])
    multiplier = float(condition.get("multiplier", 2.0))
    return volume >= avg_volume * multiplier if avg_volume > 0 else False


async def check_rsi_alert(symbol: str, condition: Dict[str, Any]) -> bool:
    """Trigger when RSI crosses a threshold."""
    history = await market_data_service.get_history(symbol, "1d", "6mo")
    if not history or len(history) < 20:
        return False
    closes = [p["close"] for p in history]
    rsi_values = compute_rsi(closes)
    if not rsi_values or rsi_values[-1] is None:
        return False
    current_rsi = rsi_values[-1]
    threshold = float(condition.get("threshold", 70))
    direction = condition.get("direction", "above")
    return current_rsi >= threshold if direction == "above" else current_rsi <= threshold
