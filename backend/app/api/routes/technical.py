from fastapi import APIRouter, Query
from typing import Any, Dict, List

from app.services.technical_service import get_combined_analysis, sma, ema, rsi, macd, bollinger_bands, generate_signals
from app.services import market_data_service

router = APIRouter()


@router.get("/{symbol}/all")
async def get_all_indicators(symbol: str, interval: str = Query("1d"), range: str = Query("1mo")):
    return await get_combined_analysis(symbol, interval, range)


@router.get("/{symbol}/sma")
async def get_sma(symbol: str, period: int = 20, interval: str = Query("1d"), range: str = Query("1mo")):
    history = await market_data_service.get_history(symbol, interval, range)
    closes = [p["close"] for p in history]
    return {"symbol": symbol.upper(), "sma": sma(closes, period)}


@router.get("/{symbol}/ema")
async def get_ema(symbol: str, period: int = 12, interval: str = Query("1d"), range: str = Query("1mo")):
    history = await market_data_service.get_history(symbol, interval, range)
    closes = [p["close"] for p in history]
    return {"symbol": symbol.upper(), "ema": ema(closes, period)}


@router.get("/{symbol}/rsi")
async def get_rsi(symbol: str, period: int = 14, interval: str = Query("1d"), range: str = Query("1mo")):
    history = await market_data_service.get_history(symbol, interval, range)
    closes = [p["close"] for p in history]
    return {"symbol": symbol.upper(), "rsi": rsi(closes, period)}


@router.get("/{symbol}/macd")
async def get_macd(symbol: str, interval: str = Query("1d"), range: str = Query("1mo")):
    history = await market_data_service.get_history(symbol, interval, range)
    closes = [p["close"] for p in history]
    return {"symbol": symbol.upper(), "macd": macd(closes)}


@router.get("/{symbol}/bollinger")
async def get_bollinger(symbol: str, interval: str = Query("1d"), range: str = Query("1mo")):
    history = await market_data_service.get_history(symbol, interval, range)
    closes = [p["close"] for p in history]
    return {"symbol": symbol.upper(), "bollinger": bollinger_bands(closes)}
