"""Real-time earnings data and news from yfinance — no database dependency.

Fetches earnings dates, estimates, historical results, and related news
on demand from yfinance.  Falls back gracefully when data is unavailable.
"""
from datetime import date, datetime, timedelta
from typing import Any, Dict, List, Optional

from app.external import yahoo_finance
from app.services import market_data_service


async def get_upcoming(symbols: Optional[List[str]] = None, days_ahead: int = 30) -> List[Dict[str, Any]]:
    """Upcoming earnings for a list of symbols (or default major ones)."""
    if not symbols:
        symbols = ["AAPL", "MSFT", "GOOGL", "AMZN", "META", "NVDA", "TSLA", "JPM", "V", "JNJ", "WMT", "XOM", "PG", "JPM", "BAC", "DIS", "ADBE", "CRM", "NFLX", "AMD"]

    results = []
    today = date.today()
    cutoff = today + timedelta(days=days_ahead)

    for symbol in symbols:
        try:
            info = await yahoo_finance.get_info(symbol)
            if not info:
                continue

            earnings_dates = info.get("earningsDate") or info.get("earningsTimestamp")
            if not earnings_dates:
                continue

            company_name = info.get("shortName") or info.get("longName") or symbol
            market_cap = info.get("marketCap")
            eps_estimate = info.get("epsTrailingTwelveMonths") or info.get("forwardEps")
            revenue = info.get("totalRevenue")

            # earningsDate can be a list of timestamps or single timestamp
            if isinstance(earnings_dates, (int, float)):
                earnings_dates = [earnings_dates]

            for dt_val in earnings_dates:
                if isinstance(dt_val, (int, float)):
                    report_date = date.fromtimestamp(dt_val)
                else:
                    continue

                if report_date < today or report_date > cutoff:
                    continue

                # Determine report timing
                try:
                    ts = datetime.fromtimestamp(dt_val)
                    hour = ts.hour
                    if hour < 12:
                        timing = "Before Market"
                    elif hour < 16:
                        timing = "During Market"
                    else:
                        timing = "After Market"
                except Exception:
                    timing = "Unknown"

                results.append({
                    "symbol": symbol,
                    "company_name": company_name,
                    "report_date": report_date.isoformat(),
                    "timing": timing,
                    "eps_estimate": float(eps_estimate) if eps_estimate else None,
                    "revenue_estimate": float(revenue) if revenue else None,
                    "previous_eps": float(info.get("epsCurrentYear")) if info.get("epsCurrentYear") else None,
                    "market_cap": market_cap,
                })
                break  # Only take the next earnings date

        except Exception:
            continue

    results.sort(key=lambda x: x["report_date"])
    return results


async def get_earnings_detail(symbol: str) -> Dict[str, Any]:
    """Detailed earnings info for a symbol: next date, history, estimates."""
    info = await yahoo_finance.get_info(symbol)
    if not info:
        return {"symbol": symbol.upper(), "error": "Data unavailable"}

    company_name = info.get("shortName") or info.get("longName") or symbol
    sector = info.get("sector")
    market_cap = info.get("marketCap")

    # Next earnings date
    next_date = None
    earnings_dates = info.get("earningsDate") or info.get("earningsTimestamp")
    if earnings_dates:
        dt_val = earnings_dates[0] if isinstance(earnings_dates, list) else earnings_dates
        if isinstance(dt_val, (int, float)):
            next_date = date.fromtimestamp(dt_val).isoformat()

    # Current estimates
    eps_estimate = info.get("epsTrailingTwelveMonths") or info.get("forwardEps")
    revenue_estimate = info.get("totalRevenue")

    # Historical earnings from earningsData structure
    history = []
    earnings_data = info.get("earningsData", {}) if isinstance(info.get("earningsData"), dict) else {}

    earnings_history = earnings_data.get("earningsList", []) if isinstance(earnings_data.get("earningsList"), list) else []
    for entry in earnings_history[:12]:
        if isinstance(entry, dict):
            history.append({
                "fiscal_quarter": entry.get("fiscalQuarter"),
                "fiscal_year": entry.get("fiscalYear"),
                "eps_actual": entry.get("epsActual"),
                "eps_estimate": entry.get("epsEstimate"),
                "eps_surprise_pct": round((float(entry["epsActual"]) - float(entry["epsEstimate"])) / abs(float(entry["epsEstimate"])) * 100, 2)
                if entry.get("epsActual") and entry.get("epsEstimate") else None,
                "report_date": str(entry.get("reportDate")) if entry.get("reportDate") else None,
            })

    # Fallback: extract from info dict
    if not history:
        for q in range(1, 5):
            actual_key = f"epsQuarterly{q}Actual"
            est_key = f"epsQuarterly{q}Estimate"
            if actual_key in info or est_key in info:
                history.append({
                    "fiscal_quarter": q,
                    "eps_actual": info.get(actual_key),
                    "eps_estimate": info.get(est_key),
                    "eps_surprise_pct": round((float(info[actual_key]) - float(info[est_key])) / abs(float(info[est_key])) * 100, 2)
                    if info.get(actual_key) and info.get(est_key) and float(info[est_key]) != 0 else None,
                })

    return {
        "symbol": symbol.upper(),
        "company_name": company_name,
        "sector": sector,
        "market_cap": market_cap,
        "next_earnings_date": next_date,
        "eps_estimate": float(eps_estimate) if eps_estimate else None,
        "revenue_estimate": float(revenue_estimate) if revenue_estimate else None,
        "price": info.get("currentPrice") or info.get("regularMarketPrice"),
        "pe_ratio": info.get("trailingPE"),
        "forward_pe": info.get("forwardPE"),
        "dividend_yield": info.get("dividendYield"),
        "history": history,
    }


async def get_news(symbol: str) -> List[Dict[str, Any]]:
    """Related news for a symbol from yfinance."""
    try:
        news = await yahoo_finance.get_info(symbol)
        news_items = news.get("news", []) if isinstance(news, dict) else []
        if not news_items:
            return []

        results = []
        for item in news_items[:10]:
            if not isinstance(item, dict):
                continue
            results.append({
                "title": item.get("title"),
                "publisher": item.get("publisher"),
                "link": item.get("link"),
                "published": datetime.fromtimestamp(item["providerPublishTime"]).isoformat()
                if item.get("providerPublishTime") else None,
                "summary": item.get("summary"),
                "type": item.get("type"),
            })
        return results
    except Exception:
        return []
