from typing import Any, Dict, List
import numpy as np
import pandas as pd

from app.services import market_data_service


def sma(data: List[float], period: int) -> List[float]:
    if len(data) < period:
        return []
    series = pd.Series(data)
    result = series.rolling(window=period).mean()
    return [None] * (period - 1) + [float(v) if not pd.isna(v) else None for v in result[period - 1:]]


def ema(data: List[float], period: int) -> List[float]:
    if len(data) < period:
        return []
    series = pd.Series(data)
    result = series.ewm(span=period, adjust=False).mean()
    return [float(v) if not pd.isna(v) else None for v in result]


def rsi(data: List[float], period: int = 14) -> List[float]:
    if len(data) < period + 1:
        return []
    series = pd.Series(data)
    delta = series.diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)
    avg_gain = gain.rolling(window=period).mean()
    avg_loss = loss.rolling(window=period).mean()
    rs = avg_gain / avg_loss
    rsi_values = 100 - (100 / (1 + rs))
    return [None] * period + [float(v) if not pd.isna(v) else None for v in rsi_values[period:]]


def macd(data: List[float], fast: int = 12, slow: int = 26, signal: int = 9) -> Dict[str, List]:
    if len(data) < slow:
        return {"macd": [], "signal": [], "histogram": []}
    series = pd.Series(data)
    ema_fast = series.ewm(span=fast, adjust=False).mean()
    ema_slow = series.ewm(span=slow, adjust=False).mean()
    macd_line = ema_fast - ema_slow
    signal_line = macd_line.ewm(span=signal, adjust=False).mean()
    histogram = macd_line - signal_line
    return {
        "macd": [float(v) if not pd.isna(v) else None for v in macd_line],
        "signal": [float(v) if not pd.isna(v) else None for v in signal_line],
        "histogram": [float(v) if not pd.isna(v) else None for v in histogram],
    }


def bollinger_bands(data: List[float], period: int = 20, std_dev: int = 2) -> Dict[str, List]:
    if len(data) < period:
        return {"upper": [], "middle": [], "lower": []}
    series = pd.Series(data)
    middle = series.rolling(window=period).mean()
    std = series.rolling(window=period).std()
    upper = middle + (std * std_dev)
    lower = middle - (std * std_dev)
    return {
        "upper": [float(v) if not pd.isna(v) else None for v in upper],
        "middle": [float(v) if not pd.isna(v) else None for v in middle],
        "lower": [float(v) if not pd.isna(v) else None for v in lower],
    }


def volume_analysis(data: List[float], volume_data: List[int]) -> Dict[str, Any]:
    if not volume_data:
        return {"volume": [], "avg_volume": None, "volume_ratio": None}
    avg_vol = np.mean(volume_data)
    latest_vol = volume_data[-1] if volume_data else 0
    ratio = latest_vol / avg_vol if avg_vol > 0 else 0
    return {"volume": volume_data, "avg_volume": float(avg_vol), "volume_ratio": float(ratio)}


def generate_signals(data: List[float]) -> List[Dict[str, str]]:
    if len(data) < 50:
        return []
    signals = []
    rsi_values = rsi(data)
    macd_data = macd(data)

    current_rsi = rsi_values[-1] if rsi_values and rsi_values[-1] is not None else 50
    if current_rsi > 70:
        signals.append({"indicator": "RSI", "signal": "bearish", "message": f"RSI at {current_rsi:.1f} (overbought)"})
    elif current_rsi < 30:
        signals.append({"indicator": "RSI", "signal": "bullish", "message": f"RSI at {current_rsi:.1f} (oversold)"})

    if macd_data.get("histogram") and len(macd_data["histogram"]) >= 2:
        prev_h = macd_data["histogram"][-2]
        curr_h = macd_data["histogram"][-1]
        if prev_h is not None and curr_h is not None:
            if prev_h < 0 and curr_h >= 0:
                signals.append({"indicator": "MACD", "signal": "bullish", "message": "MACD crossed above signal line"})
            elif prev_h > 0 and curr_h <= 0:
                signals.append({"indicator": "MACD", "signal": "bearish", "message": "MACD crossed below signal line"})

    # SMA crossover
    if len(data) > 50:
        short_sma = sma(data, 20)
        long_sma = sma(data, 50)
        if short_sma and long_sma:
            valid_short = [s for s in short_sma[-5:] if s is not None]
            valid_long = [s for s in long_sma[-5:] if s is not None]
            if len(valid_short) >= 2 and len(valid_long) >= 2:
                if valid_short[-2] <= valid_long[-2] and valid_short[-1] > valid_long[-1]:
                    signals.append({"indicator": "SMA", "signal": "bullish", "message": "SMA 20 crossed above SMA 50 (Golden Cross)"})
                elif valid_short[-2] >= valid_long[-2] and valid_short[-1] < valid_long[-1]:
                    signals.append({"indicator": "SMA", "signal": "bearish", "message": "SMA 20 crossed below SMA 50 (Death Cross)"})

    return signals


async def get_combined_analysis(symbol: str, interval: str = "1d", range_str: str = "1mo") -> Dict[str, Any]:
    history = await market_data_service.get_history(symbol, interval, range_str)
    if not history:
        return {"symbol": symbol, "error": "No data available"}

    closes = [p["close"] for p in history]
    volumes = [p["volume"] for p in history]
    dates = [p["date"] for p in history]

    return {
        "symbol": symbol.upper(),
        "dates": dates,
        "prices": closes,
        "ohlcv": history,
        "sma_20": sma(closes, 20),
        "sma_50": sma(closes, 50) if len(closes) >= 50 else [],
        "ema_12": ema(closes, 12),
        "ema_26": ema(closes, 26),
        "rsi_14": rsi(closes),
        "macd": macd(closes),
        "bollinger": bollinger_bands(closes),
        "volume": volume_analysis(closes, volumes),
        "signals": generate_signals(closes),
    }
