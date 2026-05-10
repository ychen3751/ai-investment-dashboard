"""Professional technical indicator engine using the `ta` library.

Every indicator is computed via the established `ta` library (Wilder smoothing
for RSI, EMA-based MACD, etc.) rather than hand-rolled approximations.  The
response contract matches what the frontend light weight-charts components
expect, so no frontend changes are needed.
"""
from typing import Any, Dict, List

import numpy as np
import pandas as pd
from ta.momentum import RSIIndicator
from ta.trend import MACD, SMAIndicator, EMAIndicator
from ta.volatility import BollingerBands
from ta.volume import VolumeWeightedAveragePrice

from app.services import market_data_service

# ── Helpers ──────────────────────────────────────────────────────────────


def _to_list(series: pd.Series) -> List[float]:
    """Convert a pandas Series to a Python list, replacing NaN with None."""
    return [float(v) if not pd.isna(v) else None for v in series]


def _validate(closes: List[float], min_len: int) -> bool:
    """Return False when there isn't enough data for a meaningful calculation."""
    return len(closes) >= min_len


# ── Individual indicators ────────────────────────────────────────────────


def sma(data: List[float], period: int) -> List[float]:
    if not _validate(data, period):
        return []
    return _to_list(SMAIndicator(close=pd.Series(data), window=period).sma_indicator())


def ema(data: List[float], period: int) -> List[float]:
    if not _validate(data, period):
        return []
    return _to_list(EMAIndicator(close=pd.Series(data), window=period).ema_indicator())


def rsi(data: List[float], period: int = 14) -> List[float]:
    if not _validate(data, period + 1):
        return []
    return _to_list(RSIIndicator(close=pd.Series(data), window=period).rsi())


def macd(data: List[float], fast: int = 12, slow: int = 26, signal: int = 9) -> Dict[str, List]:
    if not _validate(data, slow):
        return {"macd": [], "signal": [], "histogram": []}
    m = MACD(close=pd.Series(data), window_slow=slow, window_fast=fast, window_sign=signal)
    return {
        "macd": _to_list(m.macd()),
        "signal": _to_list(m.macd_signal()),
        "histogram": _to_list(m.macd_diff()),
    }


def bollinger_bands(data: List[float], period: int = 20, std_dev: int = 2) -> Dict[str, List]:
    if not _validate(data, period):
        return {"upper": [], "middle": [], "lower": []}
    bb = BollingerBands(close=pd.Series(data), window=period, window_dev=std_dev)
    return {
        "upper": _to_list(bb.bollinger_hband()),
        "middle": _to_list(bb.bollinger_mavg()),
        "lower": _to_list(bb.bollinger_lband()),
    }


def volume_analysis(closes: List[float], volume_data: List[int]) -> Dict[str, Any]:
    if not volume_data:
        return {"volume": [], "avg_volume": None, "volume_ratio": None}
    avg_vol = float(np.mean(volume_data))
    latest_vol = float(volume_data[-1]) if volume_data else 0
    ratio = latest_vol / avg_vol if avg_vol > 0 else 0
    return {
        "volume": volume_data,
        "avg_volume": avg_vol,
        "volume_ratio": round(ratio, 4),
    }


# ── Multi-indicator signal generation ────────────────────────────────────


def generate_signals(data: List[float]) -> List[Dict[str, str]]:
    """Generate bullish/bearish/neutral signals based on multiple indicators."""
    signals: List[Dict[str, str]] = []

    # 1. RSI — overbought / oversold
    rsi_values = rsi(data)
    if rsi_values and rsi_values[-1] is not None:
        val = rsi_values[-1]
        if val > 70:
            signals.append({"indicator": "RSI", "signal": "bearish", "message": f"RSI at {val:.1f} — overbought territory (above 70)"})
        elif val < 30:
            signals.append({"indicator": "RSI", "signal": "bullish", "message": f"RSI at {val:.1f} — oversold territory (below 30)"})
        else:
            signals.append({"indicator": "RSI", "signal": "neutral", "message": f"RSI at {val:.1f} — neutral range"})

    # 2. MACD crossover
    macd_data = macd(data)
    hist = macd_data.get("histogram", [])
    if len(hist) >= 2 and hist[-2] is not None and hist[-1] is not None:
        if hist[-2] < 0 and hist[-1] >= 0:
            signals.append({"indicator": "MACD", "signal": "bullish", "message": "MACD crossed above the signal line"})
        elif hist[-2] > 0 and hist[-1] <= 0:
            signals.append({"indicator": "MACD", "signal": "bearish", "message": "MACD crossed below the signal line"})

    # 3. SMA crossover (golden / death cross)
    if len(data) >= 50:
        short_sma = sma(data, 20)
        long_sma = sma(data, 50)
        valid_short = [s for s in short_sma[-5:] if s is not None]
        valid_long = [s for s in long_sma[-5:] if s is not None]
        if len(valid_short) >= 2 and len(valid_long) >= 2:
            if valid_short[-2] <= valid_long[-2] and valid_short[-1] > valid_long[-1]:
                signals.append({"indicator": "SMA 20/50", "signal": "bullish", "message": "Golden Cross — SMA 20 crossed above SMA 50"})
            elif valid_short[-2] >= valid_long[-2] and valid_short[-1] < valid_long[-1]:
                signals.append({"indicator": "SMA 20/50", "signal": "bearish", "message": "Death Cross — SMA 20 crossed below SMA 50"})

    # 4. Bollinger Bands — price touching bands
    bb = bollinger_bands(data)
    if len(bb["upper"]) > 0 and bb["upper"][-1] is not None and bb["lower"][-1] is not None:
        last_price = data[-1]
        upper = bb["upper"][-1]
        lower = bb["lower"][-1]
        if last_price >= upper * 0.995:
            signals.append({"indicator": "Bollinger Bands", "signal": "bearish", "message": "Price at upper Bollinger Band — potential overextension"})
        elif last_price <= lower * 1.005:
            signals.append({"indicator": "Bollinger Bands", "signal": "bullish", "message": "Price at lower Bollinger Band — potential bounce"})

    return signals


# ── Main analysis endpoint ───────────────────────────────────────────────


async def get_combined_analysis(symbol: str, interval: str = "1d", range_str: str = "1mo") -> Dict[str, Any]:
    """Fetch price history and compute all indicators in one shot.

    The returned dict is the single source of truth for the frontend's
    Technical Analysis page (candlestick chart + indicator panels + signals).
    """
    history = await market_data_service.get_history(symbol, interval, range_str)
    if not history:
        return {"symbol": symbol.upper(), "error": "No data available"}

    closes = [p["close"] for p in history]
    volumes = [p["volume"] for p in history]
    dates = [p["date"] for p in history]

    # Compute all indicators
    sma_20 = sma(closes, 20)
    sma_50 = sma(closes, 50) if len(closes) >= 50 else []
    ema_12 = ema(closes, 12)
    ema_26 = ema(closes, 26)

    return {
        "symbol": symbol.upper(),
        "dates": dates,
        "prices": closes,
        "ohlcv": history,
        "sma_20": sma_20,
        "sma_50": sma_50,
        "ema_12": ema_12,
        "ema_26": ema_26,
        "rsi_14": rsi(closes),
        "macd": macd(closes),
        "bollinger": bollinger_bands(closes),
        "volume": volume_analysis(closes, volumes),
        "signals": generate_signals(closes),
    }
