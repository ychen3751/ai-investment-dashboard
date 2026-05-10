"""Options chain analysis — fetches real option chain data from yfinance and
computes unusual activity scores.
"""
from datetime import date
from typing import Any, Dict, List, Optional

from app.external import yahoo_finance


async def get_expirations(symbol: str) -> List[str]:
    """Available expiration dates for a symbol."""
    return await yahoo_finance.get_options_expirations(symbol)


async def get_chain(symbol: str, expiration: Optional[str] = None) -> Dict[str, Any]:
    """Full option chain with computed unusual activity scores.

    Returns:
        {
            "symbol": "AAPL",
            "expiration": "2026-06-19",
            "underlying_price": 293.26,
            "calls": [ ... ],
            "puts": [ ... ],
            "timestamp": "2026-05-10T12:00:00",
        }
    """
    raw = await yahoo_finance.get_options_chain(symbol, expiration)
    return {
        "symbol": symbol.upper(),
        "expiration": expiration or "near",
        "calls": raw.get("calls", []),
        "puts": raw.get("puts", []),
    }


async def get_chain_with_scores(
    symbol: str,
    expiration: Optional[str] = None,
    min_premium: float = 0,
    option_type_filter: Optional[str] = None,
    unusual_only: bool = False,
) -> Dict[str, Any]:
    """Fetch option chain and compute unusual activity scores for each contract.

    Score components (each 0–25, total 0–100):
      - Volume / OI ratio (higher = more unusual)
      - Total premium $ (higher = more unusual)
      - Near-the-money (closer to underlying = more notable)
      - Short-dated (near expiration = more sensitive)
    """
    chain = await get_chain(symbol, expiration)
    underlying_price = 0
    try:
        from app.services import market_data_service
        quote = await market_data_service.get_quote(symbol)
        if quote:
            underlying_price = float(quote.get("price", 0))
    except Exception:
        pass

    chain_expiration = expiration

    def score_contracts(contracts: List[Dict]) -> List[Dict]:
        results = []
        for c in contracts:
            vol = c.get("volume", 0) or 0
            oi = c.get("open_interest", 0) or 0
            last = c.get("last_price", 0) or 0
            strike = c.get("strike", 0) or 0
            iv = c.get("implied_volatility", 0) or 0
            bid = c.get("bid", 0) or 0
            ask = c.get("ask", 0) or 0

            vol_oi_ratio = vol / max(oi, 1)
            premium_est = last * vol * 100

            if premium_est < min_premium:
                continue

            # Score components
            score_v = min(25, vol_oi_ratio * 10) if vol_oi_ratio > 0 else 0
            score_p = min(25, premium_est / 20000)  # $20k = 25 points
            # Near-the-money: closer = higher score
            if underlying_price > 0 and strike > 0:
                moneyness = abs(strike - underlying_price) / underlying_price
                score_m = max(0, 25 - moneyness * 100)  # 1% away = 24, 25% away = 0
            else:
                score_m = 0
            # Short-dated: within 7 days = max score
            from datetime import datetime
            exp = chain_expiration or ""
            if exp and chain_expiration:
                try:
                    exp_date = datetime.strptime(exp[:10], "%Y-%m-%d").date()
                    days_to_exp = (exp_date - date.today()).days
                    score_d = max(0, 25 - days_to_exp * 2) if days_to_exp >= 0 else 0
                except Exception:
                    score_d = 0
            else:
                score_d = 0

            total_score = round(score_v + score_p + score_m + score_d, 1)

            # Determine signal
            if total_score >= 60 and vol_oi_ratio > 2:
                signal = "Unusual Volume"
            elif total_score >= 40 and premium_est > 500000:
                signal = "High Premium"
            elif total_score >= 30:
                signal = "Abnormal Flow"
            else:
                signal = "Normal"

            results.append({
                "strike": strike,
                "expiration": c.get("expiration", expiration or ""),
                "last_price": last,
                "bid": bid,
                "ask": ask,
                "volume": vol,
                "open_interest": oi,
                "volume_oi_ratio": round(vol_oi_ratio, 2),
                "implied_volatility": round(iv * 100, 2),
                "premium": round(premium_est, 2),
                "unusual_score": total_score,
                "signal": signal,
            })

        results.sort(key=lambda x: x["unusual_score"], reverse=True)
        return results

    all_contracts = []
    if option_type_filter in (None, "call"):
        scored = score_contracts(chain.get("calls", []))
        for s in scored:
            s["option_type"] = "call"
        all_contracts.extend(scored)
    if option_type_filter in (None, "put"):
        scored = score_contracts(chain.get("puts", []))
        for s in scored:
            s["option_type"] = "put"
        all_contracts.extend(scored)

    all_contracts.sort(key=lambda x: x["unusual_score"], reverse=True)

    return {
        "symbol": symbol.upper(),
        "expiration": expiration or "near",
        "underlying_price": underlying_price,
        "contracts": all_contracts,
        "total_contracts": len(all_contracts),
    }
