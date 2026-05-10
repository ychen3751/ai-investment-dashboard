from fastapi import APIRouter, Query
from typing import List, Optional

from app.services import earnings_market_service, earnings_analysis_service

router = APIRouter()


@router.get("/upcoming")
async def get_upcoming_earnings(
    symbols: Optional[str] = Query(None, description="Comma-separated tickers"),
    days_ahead: int = Query(30, ge=1, le=90),
):
    """Upcoming earnings reports for tracked symbols.

    Returns symbol, company name, date, timing (before/after market),
    EPS estimate, revenue estimate, and market cap.
    """
    symbol_list = [s.strip().upper() for s in symbols.split(",")] if symbols else None
    return await earnings_market_service.get_upcoming(symbol_list, days_ahead)


@router.get("/{symbol}")
async def get_earnings_detail(symbol: str):
    """Detailed earnings info: next date, historical results, surprise %."""
    return await earnings_market_service.get_earnings_detail(symbol)


@router.get("/{symbol}/news")
async def get_earnings_news(symbol: str):
    """Recent news articles related to a symbol."""
    return await earnings_market_service.get_news(symbol)


@router.get("/{symbol}/analysis")
async def get_earnings_analysis(symbol: str):
    """AI-style earnings analysis: signal, factors, setup assessment.

    Evaluates EPS surprise history, revenue growth, price momentum,
    valuation, and options IV to produce a bullish/bearish/neutral/mixed/high_risk
    signal with supporting factors.  Educational only — not financial advice.
    """
    return await earnings_analysis_service.get_earnings_analysis(symbol)
