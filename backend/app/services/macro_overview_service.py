"""Macro intelligence engine — fetches live market data, computes regime signals,
sector rotation, and economic indicators.  Deterministic fallback always works.
"""
from datetime import date, datetime
from typing import Any, Dict, List, Optional, Tuple
import numpy as np

from app.core.config import settings
from app.external import yahoo_finance
from app.services import market_data_service


# ── Tracked tickers ─────────────────────────────────────────────────────

MACRO_TICKERS = [
    ("SPY", "S&P 500"),
    ("QQQ", "Nasdaq 100"),
    ("DIA", "Dow Jones"),
    ("IWM", "Russell 2000"),
    ("^VIX", "CBOE Volatility Index"),
    ("^TNX", "10Y Treasury Yield"),
    ("DX-Y.NYB", "US Dollar Index"),
    ("GLD", "Gold ETF"),
    ("CL=F", "Crude Oil"),
    ("BTC-USD", "Bitcoin"),
]


async def get_macro_overview() -> Dict[str, Any]:
    """Full macro dashboard data."""
    indicators = []
    weekly_changes: Dict[str, float] = {}

    for symbol, name in MACRO_TICKERS:
        try:
            quote = await market_data_service.get_quote(symbol)
            history = await market_data_service.get_history(symbol, "1d", "1wk")
            week_ago = history[0]["close"] if len(history) >= 2 else None

            indicator = {
                "symbol": symbol.replace("^", "").replace("=F", "").replace("-", ""),
                "name": name,
                "price": float(quote["price"]) if quote and quote.get("price") else None,
                "change": float(quote["change"]) if quote and quote.get("change") else None,
                "change_pct": float(quote["change_pct"]) if quote and quote.get("change_pct") else None,
                "week_change_pct": round((float(quote["price"]) - week_ago) / week_ago * 100, 2) if week_ago and quote and quote.get("price") else None,
                "sparkline": [p["close"] for p in history[-20:]] if len(history) >= 2 else [],
            }
            indicators.append(indicator)
            if indicator["change_pct"] is not None:
                weekly_changes[symbol] = indicator["change_pct"]
        except Exception:
            indicators.append({"symbol": symbol.replace("^", ""), "name": name, "price": None, "change": None, "change_pct": None, "week_change_pct": None, "sparkline": []})

    # ── Market Regime ───────────────────────────────────────────────────
    spy_change = next((i.get("change_pct") or 0 for i in indicators if "SPY" in i["symbol"]), 0)
    vix_level = next((i.get("price") or 20 for i in indicators if "VIX" in i["symbol"]), 20)
    tnx_level = next((i.get("price") or 4 for i in indicators if "TNX" in i["symbol"]), 4)
    qqq_change = next((i.get("change_pct") or 0 for i in indicators if "QQQ" in i["symbol"]), 0)
    spy_week = next((i.get("week_change_pct") or 0 for i in indicators if "SPY" in i["symbol"]), 0)
    iwm_change = next((i.get("change_pct") or 0 for i in indicators if "IWM" in i["symbol"]), 0)

    regime, regime_conf, regime_explanation = _determine_regime(spy_change, vix_level, tnx_level, qqq_change, spy_week, iwm_change)

    # ── Macro Signals ──────────────────────────────────────────────────
    signals = {
        "liquidity": _liquidity_signal(tnx_level),
        "inflation": _inflation_signal(tnx_level),
        "growth": _growth_signal(spy_change, iwm_change),
        "fear_greed": _fear_greed_signal(vix_level),
        "volatility": _volatility_signal(vix_level),
        "bond_market": _bond_signal(tnx_level),
    }

    # ── Sector Rotation ────────────────────────────────────────────────
    sectors = await _get_sector_rotation()

    # ── Economic Calendar ──────────────────────────────────────────────
    economic = _get_economic_calendar()

    # ── AI Analysis ────────────────────────────────────────────────────
    ai_analysis = _generate_ai_analysis(regime, signals, sectors, vix_level, tnx_level)

    # Optional OpenAI enrichment
    ai_narrative = None
    if settings.OPENAI_API_KEY and settings.OPENAI_API_KEY != "placeholder_openai_api_key":
        try:
            prompt = (
                f"Macro environment: regime={regime}, VIX={vix_level:.1f}, TNX={tnx_level:.1f}%. "
                f"Sectors: {[s['name'] for s in sectors[:3]]}. "
                f"Write 2-3 sentences. Do NOT give financial advice."
            )
            from app.external.openai_client import chat_query as openai_chat
            result = await openai_chat("MACRO", prompt, [])
            if result and "not configured" not in result:
                ai_narrative = result
        except Exception:
            pass

    return {
        "market_regime": {
            "regime": regime,
            "confidence": regime_conf,
            "explanation": regime_explanation,
            "bullish_pct": round(max(0, min(100, 50 + spy_change * 5)), 1),
        },
        "macro_indicators": indicators,
        "macro_signals": signals,
        "sector_rotation": sectors,
        "economic_events": economic,
        "ai_analysis": {
            "narrative": ai_narrative or ai_analysis["narrative"],
            "key_risks": ai_analysis["key_risks"],
            "key_opportunities": ai_analysis["key_opportunities"],
        },
    }


def _determine_regime(spy_change: float, vix: float, tnx: float, qqq_change: float, spy_week: float, iwm_change: float) -> Tuple[str, int, str]:
    if vix > 30:
        return "High Volatility", min(95, int(vix * 2)), f"VIX at {vix:.1f} indicates elevated market fear and uncertainty. Consider defensive positioning."
    if vix > 25:
        return "Caution", 65, f"VIX at {vix:.1f} suggests above-average market anxiety."
    if qqq_change > 0.5 and spy_change > 0.3 and iwm_change > 0:
        return "Risk On", 75, "Broad market strength with tech leadership and small-cap participation. Favorable for risk assets."
    if spy_change > 0.3 and spy_week > 1:
        return "AI Momentum", 70, "Technology-driven rally with broadening participation. Trend remains intact."
    if tnx > 5 and spy_change < 0:
        return "Recession Risk", 60, f"Rising yields ({tnx:.2f}%) combined with falling equities suggest growth concerns."
    if spy_change < -0.5 or iwm_change < -1:
        return "Risk Off", 65, f"Broad market weakness with small caps underperforming. Reduce risk exposure."
    return "Neutral", 40, "Mixed signals — no dominant regime. Maintain balanced positioning."


def _liquidity_signal(tnx: float) -> Dict[str, Any]:
    if tnx > 5:
        return {"signal": "bearish", "explanation": f"Rising yields ({tnx:.2f}%) tighten financial conditions"}
    if tnx > 4.5:
        return {"signal": "neutral", "explanation": f"Elevated yields ({tnx:.2f}%) — monitoring liquidity"}
    return {"signal": "bullish", "explanation": f"Yields at {tnx:.2f}% — accommodative conditions"}


def _inflation_signal(tnx: float) -> Dict[str, Any]:
    if tnx > 5:
        return {"signal": "bearish", "explanation": "Bond market pricing persistent inflation pressure"}
    if tnx > 4.5:
        return {"signal": "neutral", "explanation": "Inflation expectations moderately elevated"}
    return {"signal": "bullish", "explanation": "Inflation appears contained based on yield levels"}


def _growth_signal(spy: float, iwm: float) -> Dict[str, Any]:
    if spy > 0.5 and iwm > 0:
        return {"signal": "bullish", "explanation": "Broad market strength with small-cap participation"}
    if spy > 0:
        return {"signal": "neutral", "explanation": "Moderate growth — large caps leading"}
    return {"signal": "bearish", "explanation": "Market weakness suggests slowing growth"}


def _fear_greed_signal(vix: float) -> Dict[str, Any]:
    if vix < 15:
        return {"signal": "bullish", "explanation": "VIX below 15 — low fear, market complacency"}
    if vix < 22:
        return {"signal": "neutral", "explanation": f"VIX at {vix:.1f} — normal range"}
    return {"signal": "bearish", "explanation": f"VIX at {vix:.1f} — elevated fear"}


def _volatility_signal(vix: float) -> Dict[str, Any]:
    if vix < 15:
        return {"signal": "bullish", "explanation": "Low vol environment supports risk assets"}
    if vix < 25:
        return {"signal": "neutral", "explanation": f"VIX at {vix:.1f} — normal volatility"}
    return {"signal": "bearish", "explanation": f"VIX at {vix:.1f} — high volatility regime"}


def _bond_signal(tnx: float) -> Dict[str, Any]:
    if tnx > 5:
        return {"signal": "bearish", "explanation": "Rising yields pressure equity valuations"}
    if tnx > 4.5:
        return {"signal": "neutral", "explanation": "Bond market in transition — awaiting direction"}
    return {"signal": "bullish", "explanation": "Stable/low yields support equity valuations"}


async def _get_sector_rotation() -> List[Dict[str, Any]]:
    etfs = [
        ("XLK", "Technology"), ("XLF", "Financials"), ("XLE", "Energy"),
        ("XLV", "Healthcare"), ("XLU", "Utilities"), ("XLI", "Industrials"),
        ("XLY", "Consumer Cyclical"), ("XLP", "Consumer Defensive"),
        ("XLB", "Materials"), ("XLRE", "Real Estate"), ("XLC", "Communication"),
        ("SMH", "Semiconductors"),
    ]
    results = []
    for symbol, name in etfs:
        try:
            quote = await market_data_service.get_quote(symbol)
            history = await market_data_service.get_history(symbol, "1d", "2wk")
            week_change = None
            if len(history) >= 7:
                week_change = round((history[-1]["close"] - history[-7]["close"]) / history[-7]["close"] * 100, 2)
            results.append({
                "name": name,
                "symbol": symbol,
                "daily_pct": float(quote["change_pct"]) if quote and quote.get("change_pct") else None,
                "weekly_pct": week_change,
                "momentum": round((week_change or 0) * 0.7 + (float(quote.get("change_pct", 0) or 0)) * 0.3, 2) if week_change else None,
            })
        except Exception:
            results.append({"name": name, "symbol": symbol, "daily_pct": None, "weekly_pct": None, "momentum": None})
    results.sort(key=lambda x: (x["momentum"] or 0), reverse=True)
    return results


def _get_economic_calendar() -> List[Dict[str, Any]]:
    """Upcoming economic events with estimated dates and impact."""
    today = date.today()
    month = today.month
    year = today.year
    return [
        {"event": "CPI Report", "date": f"{year}-{month:02d}-{13 if month % 2 == 1 else 14}", "impact": "High", "volatility": "High"},
        {"event": "FOMC Meeting", "date": _next_fomc(today).isoformat() if _next_fomc(today) else "TBD", "impact": "Very High", "volatility": "Extreme"},
        {"event": "Nonfarm Payrolls", "date": f"{year}-{month:02d}-{min(7, 31)}", "impact": "High", "volatility": "High"},
        {"event": "GDP (Advance)", "date": f"{year}-{month:02d}-{25}", "impact": "High", "volatility": "Medium"},
        {"event": "PPI Report", "date": f"{year}-{month:02d}-{min(14, 28)}", "impact": "Medium", "volatility": "Medium"},
        {"event": "Retail Sales", "date": f"{year}-{month:02d}-{min(15, 28)}", "impact": "Medium", "volatility": "Medium"},
    ]


def _next_fomc(today: date) -> Optional[date]:
    months = [3, 5, 6, 7, 9, 11, 12]
    for m in months:
        d = date(today.year, m, 1)
        if d > today:
            return d
    return None


def _generate_ai_analysis(regime: str, signals: Dict, sectors: List[Dict], vix: float, tnx: float) -> Dict[str, Any]:
    narratives = {
        "Risk On": "Markets are in a risk-on regime with broad-based strength across equities. Technology and cyclical sectors are leading, suggesting investor confidence in economic growth. Low volatility and stable yields support this environment.",
        "AI Momentum": "Technology-driven momentum continues to lead markets higher. AI-related sectors are seeing disproportionate capital inflows. While the trend remains intact, investors should monitor for signs of narrowing breadth.",
        "High Volatility": "Elevated volatility indicates market uncertainty. Price swings are larger than normal, suggesting defensive positioning may be warranted. Focus on quality and low-beta exposures.",
        "Risk Off": "Risk aversion is elevated with broad market weakness. Defensive sectors are outperforming. Consider reducing exposure to cyclical assets and increasing cash or bond allocations.",
        "Recession Risk": "Rising yields combined with equity weakness suggest growing recession concerns. Credit conditions may be tightening. Defensive positioning and duration exposure may provide portfolio protection.",
        "Caution": "Market conditions warrant caution. Volatility is elevated but not extreme. Maintain balanced exposure with a defensive tilt.",
    }
    narrative = narratives.get(regime, "Mixed signals across asset classes. Maintain balanced positioning and monitor key levels.")

    risks = []
    if vix > 25:
        risks.append(f"Elevated volatility (VIX {vix:.1f}) increases whipsaw risk")
    if tnx > 5:
        risks.append("Rising yields may pressure growth stock valuations")
    if tnx > 4.5:
        risks.append("Bond market volatility could spill over into equities")

    opps = []
    if vix < 20:
        opps.append("Low volatility environment favors risk assets")
    if regime in ("Risk On", "AI Momentum"):
        opps.append("Strong momentum regime supports trend-following strategies")

    return {"narrative": narrative, "key_risks": risks, "key_opportunities": opps}
