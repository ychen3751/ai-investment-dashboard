"""Watchlist intelligence — analyzes each watched ticker for technical signals,
momentum, and risk indicators.  Fully deterministic, no LLM required.
"""
from typing import Any, Dict, List, Optional
import numpy as np

from app.services import market_data_service
from app.services.technical_service import rsi as compute_rsi, sma, macd as compute_macd


async def get_signals(symbols: List[str]) -> List[Dict[str, Any]]:
    """Compute intelligence signals for a list of watchlist tickers."""
    results = []
    for symbol in symbols:
        try:
            signal = await _analyze_ticker(symbol)
            results.append(signal)
        except Exception:
            results.append({
                "ticker": symbol, "signal": "unknown", "confidence": 0,
                "summary": "Data unavailable", "indicators": {},
            })
    results.sort(key=lambda x: x["confidence"], reverse=True)
    return results


async def _analyze_ticker(symbol: str) -> Dict[str, Any]:
    """Single-ticker analysis: trend, RSI, volume, MA crossovers."""
    quote = await market_data_service.get_quote(symbol)
    history = await market_data_service.get_history(symbol, "1d", "6mo")
    if not history or len(history) < 30:
        return {
            "ticker": symbol, "signal": "insufficient_data", "confidence": 0,
            "summary": "Not enough price history", "indicators": {},
        }

    closes = [p["close"] for p in history]
    volumes = [p["volume"] for p in history]
    last_price = closes[-1]
    change_pct = float(quote.get("change_pct", 0)) if quote else 0
    volume = int(quote.get("volume", 0)) if quote else 0

    # RSI
    rsi_vals = compute_rsi(closes)
    rsi_val = rsi_vals[-1] if rsi_vals and rsi_vals[-1] is not None else 50

    # MACD
    macd_data = compute_macd(closes)
    macd_hist = macd_data.get("histogram", [])
    macd_signal = "neutral"
    if len(macd_hist) >= 2 and macd_hist[-1] is not None and macd_hist[-2] is not None:
        if macd_hist[-1] > 0 and macd_hist[-1] > macd_hist[-2]:
            macd_signal = "bullish"
        elif macd_hist[-1] < 0 and macd_hist[-1] < macd_hist[-2]:
            macd_signal = "bearish"

    # Volume spike
    avg_vol = float(np.mean(volumes[-20:])) if len(volumes) >= 20 else 0
    volume_spike = bool(volume > avg_vol * 1.5) if avg_vol > 0 else False

    # SMA crossovers
    sma20 = sma(closes, 20)
    sma50 = sma(closes, 50) if len(closes) >= 50 else []
    above_sma20 = last_price > (sma20[-1] if sma20 and sma20[-1] else 0)
    above_sma50 = last_price > (sma50[-1] if sma50 and sma50[-1] else 0)
    trend = "uptrend" if above_sma20 and above_sma50 else "downtrend" if not above_sma20 and not above_sma50 else "mixed"

    # Price change momentum
    day_pct = change_pct
    week_pct = (last_price - closes[0]) / closes[0] * 100 if len(closes) >= 5 else 0

    # Earnings countdown placeholder (would need earnings_date from info)
    earnings_soon = None

    # ── Signal determination ───────────────────────────────────────────
    signal_type, confidence, summary = _determine_signal(
        rsi_val, macd_signal, volume_spike, trend, day_pct, week_pct, above_sma20, above_sma50
    )

    # ── Momentum score (0-100) ─────────────────────────────────────────
    momentum = _momentum_score(rsi_val, macd_signal, volume_spike, trend, day_pct, week_pct)

    return {
        "ticker": symbol.upper(),
        "signal": signal_type,
        "confidence": confidence,
        "summary": summary,
        "momentum_score": int(momentum),
        "trend": trend,
        "indicators": {
            "rsi": float(round(rsi_val, 1)),
            "macd": macd_signal,
            "volume_spike": bool(volume_spike),
            "above_sma20": bool(above_sma20),
            "above_sma50": bool(above_sma50),
            "day_change_pct": float(round(day_pct, 2)),
            "week_change_pct": float(round(week_pct, 2)),
        },
    }


def _determine_signal(
    rsi: float, macd: str, vol_spike: bool, trend: str,
    day_pct: float, week_pct: float, above_sma20: bool, above_sma50: bool,
) -> tuple:
    if rsi > 75 and macd == "bullish" and vol_spike:
        return "bullish_breakout", 85, "Strong bullish momentum with above-average volume — possible breakout"
    if rsi > 70 and not above_sma50:
        return "overbought_warning", 60, "RSI overbought in a downtrend — caution warranted"
    if rsi > 70:
        return "overbought_warning", 55, f"RSI at {rsi:.0f} — overbought territory"
    if rsi < 30 and macd == "bullish" and day_pct > 0:
        return "oversold_bounce", 75, f"RSI at {rsi:.0f} with improving MACD — potential bounce"
    if rsi < 30:
        return "oversold_bounce", 60, f"RSI at {rsi:.0f} — oversold territory"
    if rsi < 35 and macd == "bearish":
        return "bearish_breakdown", 65, "RSI weak and MACD bearish — continued downside risk"
    if vol_spike and day_pct < -2:
        return "bearish_breakdown", 70, "High volume selloff — distribution possibly underway"
    if vol_spike and day_pct > 2:
        return "bullish_breakout", 70, "Above-average volume with strong price gains"
    if trend == "downtrend":
        return "bearish_breakdown", 50, "Price below both 20 and 50-day moving averages"
    if trend == "uptrend":
        return "bullish_breakout", 50, "Price above both 20 and 50-day moving averages"
    return "neutral", 30, "No significant signals detected"


def _momentum_score(rsi: float, macd: str, vol_spike: bool, trend: str, day_pct: float, week_pct: float) -> int:
    score = 50
    if rsi > 60: score += 10
    if rsi > 75: score += 10
    if rsi < 40: score -= 10
    if rsi < 25: score -= 10
    if macd == "bullish": score += 10
    if macd == "bearish": score -= 10
    if vol_spike and day_pct > 1: score += 10
    if vol_spike and day_pct < -1: score -= 10
    if trend == "uptrend": score += 10
    if trend == "downtrend": score -= 10
    if week_pct > 5: score += 5
    if week_pct < -5: score -= 5
    return max(0, min(100, score))
