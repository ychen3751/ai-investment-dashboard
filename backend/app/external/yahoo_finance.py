import yfinance as yf
import pandas as pd
from typing import Any, Dict, List, Optional
from app.external.rate_limiter import get_rate_limiter


async def get_quote(symbol: str) -> Optional[Dict[str, Any]]:
    limiter = get_rate_limiter("yfinance")
    await limiter.wait()
    try:
        ticker = yf.Ticker(symbol)
        info = ticker.info if hasattr(ticker, 'info') else {}
        if not info or 'currentPrice' not in info:
            return None
        return {
            "symbol": symbol.upper(),
            "price": info.get("currentPrice") or info.get("regularMarketPrice"),
            "previous_close": info.get("previousClose") or info.get("regularMarketPreviousClose"),
            "change": info.get("regularMarketChange"),
            "change_pct": info.get("regularMarketChangePercent"),
            "volume": info.get("volume") or info.get("regularMarketVolume"),
            "avg_volume": info.get("averageVolume"),
            "market_cap": info.get("marketCap"),
            "pe_ratio": info.get("trailingPE"),
            "dividend_yield": info.get("dividendYield"),
            "high_52w": info.get("fiftyTwoWeekHigh"),
            "low_52w": info.get("fiftyTwoWeekLow"),
            "name": info.get("shortName") or info.get("longName"),
        }
    except Exception:
        return None


async def get_history(symbol: str, interval: str = "1d", range_str: str = "1mo") -> List[Dict[str, Any]]:
    limiter = get_rate_limiter("yfinance")
    await limiter.wait()
    try:
        ticker = yf.Ticker(symbol)
        df = ticker.history(interval=interval, period=range_str)
        if df.empty:
            return []
        df.reset_index(inplace=True)
        records = []
        for _, row in df.iterrows():
            records.append({
                "date": row["Date"].isoformat() if hasattr(row["Date"], 'isoformat') else str(row["Date"]),
                "open": round(float(row["Open"]), 2),
                "high": round(float(row["High"]), 2),
                "low": round(float(row["Low"]), 2),
                "close": round(float(row["Close"]), 2),
                "volume": int(row["Volume"]),
            })
        return records
    except Exception:
        return []


async def get_info(symbol: str) -> Dict[str, Any]:
    limiter = get_rate_limiter("yfinance")
    await limiter.wait()
    try:
        ticker = yf.Ticker(symbol)
        info = ticker.info if hasattr(ticker, 'info') else {}
        return info
    except Exception:
        return {}


async def get_options_chain(symbol: str, expiration: Optional[str] = None) -> Dict[str, Any]:
    limiter = get_rate_limiter("yfinance")
    await limiter.wait()
    try:
        ticker = yf.Ticker(symbol)
        if expiration:
            chain = ticker.option_chain(expiration)
        else:
            expirations = ticker.options
            if not expirations:
                return {"calls": [], "puts": []}
            chain = ticker.option_chain(expirations[0])

        def parse_contracts(df: pd.DataFrame) -> List[Dict]:
            contracts = []
            for _, row in df.iterrows():
                contracts.append({
                    "strike": float(row["strike"]),
                    "expiration": str(row["expiration"]) if hasattr(row["expiration"], 'isoformat') else str(row["expiration"]),
                    "last_price": float(row["lastPrice"]),
                    "bid": float(row["bid"]),
                    "ask": float(row["ask"]),
                    "volume": int(row["volume"]),
                    "open_interest": int(row["openInterest"]),
                    "implied_volatility": float(row["impliedVolatility"]),
                    "premium": float(row["lastPrice"]) * int(row["volume"]) if row["volume"] > 0 else 0,
                    "volume_oi_ratio": round(int(row["volume"]) / max(int(row["openInterest"]), 1), 4),
                })
            return contracts

        return {
            "calls": parse_contracts(chain.calls),
            "puts": parse_contracts(chain.puts),
        }
    except Exception:
        return {"calls": [], "puts": []}


async def search_symbols(query: str) -> List[Dict[str, str]]:
    """Search for symbols using yfinance's search."""
    limiter = get_rate_limiter("yfinance")
    await limiter.wait()
    try:
        result = yf.Search(query)
        quotes = result.quotes if hasattr(result, 'quotes') else []
        matches = []
        seen = set()
        for q in quotes:
            symbol = q.get("symbol", "")
            if symbol and symbol not in seen:
                seen.add(symbol)
                matches.append({
                    "symbol": symbol,
                    "name": q.get("shortname") or q.get("longname") or "",
                    "exchange": q.get("exchange") or "",
                    "type": q.get("quoteType") or "",
                })
        return matches[:10]
    except Exception:
        return []


async def get_options_expirations(symbol: str) -> List[str]:
    limiter = get_rate_limiter("yfinance")
    await limiter.wait()
    try:
        ticker = yf.Ticker(symbol)
        return list(ticker.options) if ticker.options else []
    except Exception:
        return []
