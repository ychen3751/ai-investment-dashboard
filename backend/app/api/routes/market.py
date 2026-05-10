from fastapi import APIRouter, Query
from fastapi.responses import JSONResponse

from app.services import market_service

router = APIRouter()


@router.get("/quote/{symbol}")
async def get_quote(symbol: str):
    """Current price, change, volume. Cached 5 min."""
    result = await market_service.get_quote(symbol)
    if result is None:
        return JSONResponse(status_code=404, content={"detail": f"Symbol '{symbol.upper()}' not found or no data available"})
    return result


@router.get("/history/{symbol}")
async def get_history(
    symbol: str,
    interval: str = Query("1d", description="1m, 5m, 15m, 30m, 1h, 1d, 1wk, 1mo"),
    range: str = Query("1mo", description="1d, 5d, 1mo, 3mo, 6mo, 1y, 2y, 5y, max"),
):
    """OHLCV time series. Cached 5 min."""
    return await market_service.get_history(symbol, interval, range)


@router.get("/info/{symbol}")
async def get_info(symbol: str):
    """Company metadata (name, sector, industry, market cap). Cached 1 hr."""
    result = await market_service.get_info(symbol)
    if not result:
        return JSONResponse(status_code=404, content={"detail": f"Symbol '{symbol.upper()}' not found"})
    return result


@router.get("/fundamentals/{symbol}")
async def get_fundamentals(symbol: str):
    """Structured fundamentals: valuation, profitability, growth, risk, price targets.

    Returns a curated payload (not raw yfinance blob).  Cached 10 min.
    """
    result = await market_service.get_fundamentals(symbol)
    if result is None:
        return JSONResponse(status_code=404, content={"detail": f"Symbol '{symbol.upper()}' not found or no fundamental data available"})
    return result


@router.get("/search")
async def search(q: str = Query("", min_length=1)):
    """Symbol / company name search."""
    return await market_service.search_symbols(q)
