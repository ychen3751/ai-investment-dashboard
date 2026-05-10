"""Centralized market data service with Redis caching and yfinance integration.

Every public function in this module:
  - Checks Redis cache first (TTL documented per function)
  - Falls back to yfinance on cache miss
  - Stores result in Redis for subsequent calls
  - Returns clean dicts (never raw yfinance info blobs)
"""
import json
from decimal import Decimal
from typing import Any, Dict, List, Optional

from app.external import yahoo_finance
from app.core.cache import get_redis

# ── TTL constants (in seconds) ──────────────────────────────────────────
TTL_QUOTE = 300        # 5 min — price changes slowly enough
TTL_HISTORY = 300      # 5 min — historical bars are static
TTL_INFO = 3600        # 1 hr  — company metadata rarely changes
TTL_FUNDAMENTALS = 600  # 10 min — financial data


# ── Quote ────────────────────────────────────────────────────────────────

async def get_quote(symbol: str) -> Optional[Dict[str, Any]]:
    """Current price, change, volume. Cached 5 min."""
    redis = await get_redis()
    cache_key = f"quote:{symbol.upper()}"
    cached = await redis.get(cache_key)
    if cached:
        return json.loads(cached)

    result = await yahoo_finance.get_quote(symbol)
    if result:
        await redis.setex(cache_key, TTL_QUOTE, json.dumps(result, default=str))
    return result


# ── History (OHLCV) ──────────────────────────────────────────────────────

async def get_history(symbol: str, interval: str = "1d", range_str: str = "1mo") -> List[Dict[str, Any]]:
    """OHLCV bars. Cached 5 min."""
    redis = await get_redis()
    cache_key = f"hist:{symbol.upper()}:{interval}:{range_str}"
    cached = await redis.get(cache_key)
    if cached:
        return json.loads(cached)

    result = await yahoo_finance.get_history(symbol, interval, range_str)
    if result:
        await redis.setex(cache_key, TTL_HISTORY, json.dumps(result, default=str))
    return result


# ── Company info (lightweight) ───────────────────────────────────────────

async def get_info(symbol: str) -> Dict[str, Any]:
    """Key company metadata (name, sector, industry, market-cap …). Cached 1 hr."""
    redis = await get_redis()
    cache_key = f"info:{symbol.upper()}"
    cached = await redis.get(cache_key)
    if cached:
        return json.loads(cached)

    result = await yahoo_finance.get_info(symbol)
    if result:
        await redis.setex(cache_key, TTL_INFO, json.dumps(result, default=str))
    return result


# ── Fundamentals (structured investment metrics) ─────────────────────────

async def get_fundamentals(symbol: str) -> Optional[Dict[str, Any]]:
    """Structured fundamental data: valuation, profitability, growth, risk.

    Returns None only when the ticker is completely invalid.  Cached 10 min.
    """
    redis = await get_redis()
    cache_key = f"fundamentals:{symbol.upper()}"
    cached = await redis.get(cache_key)
    if cached:
        return json.loads(cached)

    raw = await yahoo_finance.get_info(symbol)
    if not raw:
        return None

    # Detect genuinely invalid tickers: missing name AND missing price data
    has_name = bool(raw.get("shortName") or raw.get("longName"))
    has_price = bool(raw.get("currentPrice") or raw.get("regularMarketPrice"))
    if not has_name and not has_price:
        return None

    result = _extract_fundamentals(symbol, raw)
    await redis.setex(cache_key, TTL_FUNDAMENTALS, json.dumps(result, default=str))
    return result


def _extract_fundamentals(symbol: str, info: Dict[str, Any]) -> Dict[str, Any]:
    """Build a clean fundamental-data payload from the raw yfinance info dict.

    This protects consumers from the 150+‑key firehose that yfinance returns.
    """
    def _d(v: Any) -> Optional[float]:
        """Safely coerce to float or None."""
        if v is None:
            return None
        try:
            return float(v)
        except (ValueError, TypeError):
            return None

    current_price = _d(info.get("currentPrice")) or _d(info.get("regularMarketPrice")) or 0

    return {
        "symbol": symbol.upper(),
        "company": {
            "name": info.get("shortName") or info.get("longName") or symbol,
            "sector": info.get("sector"),
            "industry": info.get("industry"),
            "employees": _d(info.get("fullTimeEmployees")),
            "country": info.get("country"),
            "website": info.get("website"),
            "description": info.get("longBusinessSummary"),
        },
        "valuation": {
            "market_cap": _d(info.get("marketCap")),
            "enterprise_value": _d(info.get("enterpriseValue")),
            "pe_ratio_ttm": _d(info.get("trailingPE")),
            "pe_ratio_forward": _d(info.get("forwardPE")),
            "peg_ratio": _d(info.get("pegRatio")),
            "price_to_book": _d(info.get("priceToBook")),
            "price_to_sales": _d(info.get("priceToSalesTrailing12Months")),
            "ev_to_ebitda": _d(info.get("enterpriseToEbitda")),
            "ev_to_revenue": _d(info.get("enterpriseToRevenue")),
        },
        "price": {
            "current": current_price,
            "target_mean": _d(info.get("targetMeanPrice")),
            "target_high": _d(info.get("targetHighPrice")),
            "target_low": _d(info.get("targetLowPrice")),
            "52w_high": _d(info.get("fiftyTwoWeekHigh")),
            "52w_low": _d(info.get("fiftyTwoWeekLow")),
            "50d_avg": _d(info.get("fiftyDayAverage")),
            "200d_avg": _d(info.get("twoHundredDayAverage")),
            "beta": _d(info.get("beta")),
            "short_ratio": _d(info.get("shortRatio")),
        },
        "dividends": {
            "yield_pct": _d(info.get("dividendYield")),
            "rate": _d(info.get("dividendRate")),
            "payout_ratio": _d(info.get("payoutRatio")),
            "ex_date": str(info.get("exDividendDate")) if info.get("exDividendDate") else None,
        },
        "profitability": {
            "profit_margin": _d(info.get("profitMargins")),
            "operating_margin": _d(info.get("operatingMargins")),
            "roa": _d(info.get("returnOnAssets")),
            "roe": _d(info.get("returnOnEquity")),
            "revenue": _d(info.get("totalRevenue")),
            "revenue_per_share": _d(info.get("revenuePerShare")),
            "gross_profit": _d(info.get("grossProfits")),
            "ebitda": _d(info.get("ebitda")),
            "net_income": _d(info.get("netIncomeToCommon")),
        },
        "growth": {
            "revenue_growth": _d(info.get("revenueGrowth")),
            "earnings_growth": _d(info.get("earningsGrowth")),
            "earnings_quarterly_growth": _d(info.get("earningsQuarterlyGrowth")),
        },
        "risk": {
            "debt_to_equity": _d(info.get("debtToEquity")),
            "current_ratio": _d(info.get("currentRatio")),
            "quick_ratio": _d(info.get("quickRatio")),
            "book_value": _d(info.get("bookValue")),
        },
    }


# ── Symbol search ────────────────────────────────────────────────────────

async def search_symbols(query: str) -> List[Dict[str, str]]:
    if not query or len(query.strip()) < 1:
        return []
    return await yahoo_finance.search_symbols(query)


# ── Tracked symbols (used by price poller + WebSocket) ───────────────────

async def get_tracked_symbols() -> List[str]:
    redis = await get_redis()
    symbols = await redis.smembers("tracked_symbols")
    return list(symbols) if symbols else []


async def add_tracked_symbol(symbol: str):
    redis = await get_redis()
    await redis.sadd("tracked_symbols", symbol.upper())
