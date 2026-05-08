from fastapi import APIRouter, Query
from typing import Any, Dict, List, Optional

from app.services import market_data_service

router = APIRouter()


@router.get("/quote/{symbol}")
async def get_quote(symbol: str) -> Optional[Dict[str, Any]]:
    return await market_data_service.get_quote(symbol)


@router.get("/history/{symbol}")
async def get_history(
    symbol: str,
    interval: str = Query("1d", description="1m, 5m, 15m, 30m, 1h, 1d, 1wk, 1mo"),
    range: str = Query("1mo", description="1d, 5d, 1mo, 3mo, 6mo, 1y, 2y, 5y, max"),
) -> List[Dict[str, Any]]:
    return await market_data_service.get_history(symbol, interval, range)


@router.get("/info/{symbol}")
async def get_info(symbol: str) -> Dict[str, Any]:
    return await market_data_service.get_info(symbol)


@router.get("/search")
async def search(q: str = Query("", min_length=1)) -> List[Dict[str, str]]:
    return await market_data_service.search_symbols(q)
