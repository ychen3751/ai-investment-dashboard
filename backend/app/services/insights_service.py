"""Portfolio insights engine — generates natural-language analysis of portfolio
health, risk, and performance.  Fully deterministic (no LLM required) with
optional OpenAI enrichment when configured.

All insights are observational — they describe what the data shows without
making predictions or giving financial advice.
"""
from typing import Any, Dict, List, Optional, Tuple
import numpy as np
import pandas as pd

from app.core.config import settings
from app.external import openai_client
from app.services import market_data_service


# ── Helpers ──────────────────────────────────────────────────────────────

def _safe_float(v: Any) -> float:
    try:
        x = float(v)
        return x if np.isfinite(x) else 0.0
    except (TypeError, ValueError):
        return 0.0


def _pct(n: float) -> str:
    """Format as signed percentage."""
    return f"{n:+.2f}%" if abs(n) > 0.01 else "0.00%"


def _pct_abs(n: float) -> str:
    """Format as unsigned percentage."""
    return f"{abs(n):.2f}%"


# ── Deterministic insight generators ─────────────────────────────────────

def concentration_insight(holdings_data: List[Dict]) -> Dict[str, Any]:
    """HHI, top-holding weight, plain-English explanation."""
    total = sum(_safe_float(h.get("market_value", 0)) for h in holdings_data)
    if total <= 0:
        return {"label": "Concentration", "summary": "No position data available.", "severity": "neutral"}

    weights = [_safe_float(h.get("market_value", 0)) / total for h in holdings_data]
    hhi = int(sum(w ** 2 for w in weights) * 10000)
    top = max(weights) * 100
    holdings_count = len(holdings_data)

    if hhi > 2500:
        severity = "high"
        summary = f"Portfolio is highly concentrated — top holding is {top:.0f}% of total value."
        detail = f"With only {holdings_count} position{'s' if holdings_count > 1 else ''} and an HHI of {hhi}, a single significant decline would have an outsized impact."
    elif hhi > 1500:
        severity = "medium"
        summary = f"Portfolio shows moderate concentration (HHI {hhi})."
        detail = f"The largest position represents {top:.1f}% of assets. Adding uncorrelated positions would reduce single-name risk."
    else:
        severity = "low"
        summary = f"Portfolio is well-diversified across {holdings_count} positions (HHI {hhi})."
        detail = "No single holding dominates, which helps reduce idiosyncratic risk."

    return {"label": "Concentration Risk", "summary": summary, "detail": detail, "severity": severity}


def sector_insight(holdings_data: List[Dict]) -> Dict[str, Any]:
    """Sector exposure from yfinance info (best-effort)."""
    total = sum(_safe_float(h.get("market_value", 0)) for h in holdings_data)
    if total <= 0:
        return {"label": "Sector Exposure", "summary": "No position data.", "severity": "neutral"}

    sectors: Dict[str, float] = {}
    unknown_value = 0.0
    for h in holdings_data:
        mv = _safe_float(h.get("market_value", 0))
        # Sector info comes pre-fetched in holdings under "sector" if available
        sector = h.get("sector")
        if sector:
            sectors[sector] = sectors.get(sector, 0) + mv
        else:
            unknown_value += mv

    if not sectors:
        return {"label": "Sector Exposure", "summary": "Sector data unavailable for these holdings.", "severity": "neutral"}

    top_sector = max(sectors, key=sectors.get)
    top_pct = sectors[top_sector] / total * 100
    num_sectors = len(sectors)

    if num_sectors <= 2 and top_pct > 80:
        severity = "high"
        summary = f"Portfolio is concentrated in {num_sectors} sector{'s' if num_sectors > 1 else ''} ({top_pct:.0f}% in {top_sector})."
        detail = "Sector-specific downturns could significantly impact the entire portfolio."
    elif top_pct > 50:
        severity = "medium"
        summary = f"{top_sector} represents {top_pct:.0f}% of the portfolio across {num_sectors} sectors."
        detail = "Consider adding exposure to other sectors for better macro diversification."
    else:
        severity = "low"
        summary = f"Portfolio spans {num_sectors} sectors with {top_sector} as the largest ({top_pct:.0f}%)."
        detail = "Sector diversification is reasonable."

    return {"label": "Sector Exposure", "summary": summary, "detail": detail, "severity": severity}


def volatility_insight(daily_vol_pct: Optional[float], ann_vol_pct: Optional[float]) -> Dict[str, Any]:
    """Volatility observation vs typical market ranges."""
    if ann_vol_pct is None or daily_vol_pct is None:
        return {"label": "Volatility", "summary": "Insufficient history to assess.", "severity": "neutral"}

    if ann_vol_pct > 40:
        severity = "high"
        summary = f"Annualized volatility of {ann_vol_pct:.1f}% is well above the typical S&P 500 range (15–20%)."
        detail = "Daily moves above 2% are common. Position sizing should account for this variability."
    elif ann_vol_pct > 25:
        severity = "medium"
        summary = f"Annualized volatility of {ann_vol_pct:.1f}% is moderately above market averages."
        detail = "The portfolio experiences larger daily swings than a broad-market index."
    else:
        severity = "low"
        summary = f"Annualized volatility of {ann_vol_pct:.1f}% is in a moderate range."
        detail = "Daily price movements are broadly in line with diversified equity exposure."

    return {"label": "Volatility", "summary": summary, "detail": detail, "severity": severity}


def top_contributors_insight(holdings_data: List[Dict]) -> Dict[str, Any]:
    """Best and worst performers by total P&L."""
    performers = []
    for h in holdings_data:
        pnl_pct = _safe_float(h.get("total_pnl_pct"))
        if pnl_pct != 0:
            performers.append({"symbol": h["symbol"], "pnl_pct": pnl_pct, "pnl": _safe_float(h.get("total_pnl"))})

    if not performers:
        return {"label": "Performance", "summary": "No P&L data available.", "severity": "neutral"}

    performers.sort(key=lambda x: x["pnl_pct"], reverse=True)
    best = performers[0]
    worst = performers[-1]

    lines = []
    if best["pnl_pct"] > 5:
        lines.append(f"{best['symbol']} is the top performer ({_pct(best['pnl_pct'])}).")
    if worst["pnl_pct"] < -5:
        lines.append(f"{worst['symbol']} is the weakest position ({_pct(worst['pnl_pct'])}).")

    if len(performers) >= 2:
        spread = best["pnl_pct"] - worst["pnl_pct"]
        if spread > 50:
            lines.append(f"Return dispersion is wide ({_pct_abs(spread)}) — performance is being driven by a narrow set of holdings.")

    if not lines:
        return {"label": "Performance", "summary": "Performance is relatively uniform across holdings.", "severity": "low"}

    return {"label": "Performance", "summary": " ".join(lines), "detail": f"Best: {best['symbol']} {_pct(best['pnl_pct'])} / Worst: {worst['symbol']} {_pct(worst['pnl_pct'])}", "severity": "low"}


def diversification_insight(holdings_data: List[Dict], correlation: Optional[List[List[float]]]) -> Dict[str, Any]:
    """Diversification assessment based on count and correlation."""
    n = len(holdings_data)
    if n == 0:
        return {"label": "Diversification", "summary": "No holdings to assess.", "severity": "neutral"}

    if n == 1:
        return {"label": "Diversification", "summary": "Single-position portfolio — entirely dependent on one name.", "severity": "high"}

    if n <= 3:
        return {"label": "Diversification", "summary": f"Only {n} positions — the portfolio lacks meaningful diversification.", "severity": "high"}

    if n <= 5:
        return {"label": "Diversification", "summary": f"{n} positions provide moderate diversification but concentrated risk remains.", "severity": "medium"}

    has_low_correlation = False
    if correlation and len(correlation) >= 2:
        off_diag = []
        for i in range(len(correlation)):
            for j in range(len(correlation)):
                if i < j:
                    off_diag.append(abs(correlation[i][j]))
        if off_diag:
            avg_corr = np.mean(off_diag)
            if avg_corr < 0.3:
                has_low_correlation = True

    if has_low_correlation:
        return {"label": "Diversification", "summary": f"{n} positions with low average correlation — good diversification.", "severity": "low"}

    return {"label": "Diversification", "summary": f"{n} positions provide broad diversification.", "severity": "low"}


def beta_insight(beta: Optional[float]) -> Dict[str, Any]:
    """Beta observation vs SPY."""
    if beta is None:
        return {"label": "Market Sensitivity", "summary": "Beta data unavailable.", "severity": "neutral"}

    if beta > 1.3:
        severity = "high"
        summary = f"Beta of {beta:.2f} means the portfolio amplifies market moves by {(beta - 1) * 100:.0f}%."
        detail = "In a market downturn, this portfolio would likely decline more than the S&P 500."
    elif beta > 0.8:
        severity = "medium"
        summary = f"Beta of {beta:.2f} — portfolio moves broadly in line with the market."
        detail = "Market direction is a meaningful driver of portfolio performance."
    else:
        severity = "low"
        summary = f"Beta of {beta:.2f} — portfolio is less sensitive to broad market movements."
        detail = "The portfolio may hold its value better during market declines."

    return {"label": "Market Sensitivity", "summary": summary, "detail": detail, "severity": severity}


def momentum_insight(holdings_data: List[Dict]) -> Dict[str, Any]:
    """Recent price momentum from yfinance (5-day and 20-day lookback)."""
    gains_5d = 0
    losses_5d = 0
    total_5d = 0

    for h in holdings_data:
        mv = _safe_float(h.get("market_value", 0))
        if mv <= 0:
            continue
        day_pct = _safe_float(h.get("day_change_pct", 0))
        total_5d += mv
        if day_pct > 0:
            gains_5d += mv
        else:
            losses_5d += mv

    if total_5d <= 0:
        return {"label": "Momentum", "summary": "Price data unavailable.", "severity": "neutral"}

    advancing_pct = gains_5d / total_5d * 100

    if advancing_pct > 70:
        severity = "positive"
        summary = f"Broad upward momentum — {advancing_pct:.0f}% of holdings by value advanced today."
        detail = "Strong participation suggests broad-based positive sentiment."
    elif advancing_pct > 55:
        severity = "positive"
        summary = f"Slightly positive day — {advancing_pct:.0f}% of holdings by value are up."
    elif advancing_pct > 40:
        severity = "negative"
        summary = f"Slightly negative day — {100 - advancing_pct:.0f}% of holdings by value declined."
    else:
        severity = "negative"
        summary = f"Broad weakness — only {advancing_pct:.0f}% of holdings by value advanced today."
        detail = "Widespread selling pressure across positions."

    return {"label": "Momentum", "summary": summary, "detail": detail, "severity": severity}


# ── Main insight generator ───────────────────────────────────────────────

async def get_portfolio_insights(holdings_data: List[Dict]) -> Dict[str, Any]:
    """Generate all portfolio insights from holdings data.

    `holdings_data` should contain dicts with keys:
        symbol, market_value, total_cost, total_pnl, total_pnl_pct,
        day_change_pct, sector (optional, from yfinance info)
    """
    # Enrich with sector data from yfinance (best-effort, cached)
    import asyncio

    async def _enrich(h: Dict) -> Dict:
        if "sector" not in h or not h["sector"]:
            try:
                info = await market_data_service.get_info(h["symbol"])
                if isinstance(info, dict):
                    h["sector"] = info.get("sector") or "Other"
            except Exception:
                pass
        return h

    holdings_data = await asyncio.gather(*[_enrich(h) for h in holdings_data])

    insights = {}

    # 1. Concentration
    insights["concentration"] = concentration_insight(holdings_data)

    # 2. Sector exposure
    insights["sector"] = sector_insight(holdings_data)

    # 3. Top contributors / weakest
    insights["performance"] = top_contributors_insight(holdings_data)

    # 4. Momentum
    insights["momentum"] = momentum_insight(holdings_data)

    # 5. Try to enrich with volatility, beta, correlation from risk data
    try:
        from app.services.risk_service import get_risk_summary
        risk_data = await get_risk_summary(holdings_data)
        if "error" not in risk_data:
            insights["volatility"] = volatility_insight(
                risk_data.get("volatility", {}).get("daily"),
                risk_data.get("volatility", {}).get("annualized"),
            )
            insights["beta"] = beta_insight(
                risk_data.get("beta", {}).get("beta") if isinstance(risk_data.get("beta"), dict) else None
            )

            # Diversification using correlation matrix
            try:
                from app.services.risk_service import get_correlation_matrix
                corr_data = await get_correlation_matrix(holdings_data)
                corr_matrix = corr_data.get("matrix") if "error" not in corr_data else None
            except Exception:
                corr_matrix = None
            insights["diversification"] = diversification_insight(holdings_data, corr_matrix)
        else:
            insights["volatility"] = {"label": "Volatility", "summary": "Insufficient history to assess.", "severity": "neutral"}
            insights["beta"] = {"label": "Market Sensitivity", "summary": "Beta data unavailable.", "severity": "neutral"}
            insights["diversification"] = diversification_insight(holdings_data, None)
    except Exception:
        insights["volatility"] = {"label": "Volatility", "summary": "Could not compute.", "severity": "neutral"}
        insights["beta"] = {"label": "Market Sensitivity", "summary": "Could not compute.", "severity": "neutral"}
        insights["diversification"] = diversification_insight(holdings_data, None)

    # 6. Optional OpenAI enrichment (if key configured)
    insights["ai_enriched"] = False
    if settings.OPENAI_API_KEY and settings.OPENAI_API_KEY != "placeholder_openai_api_key":
        try:
            symbols = [h["symbol"] for h in holdings_data]
            summary_text = "; ".join(
                v["summary"] for v in insights.values() if isinstance(v, dict) and "summary" in v
            )
            prompt = (
                f"Portfolio insights:\n{summary_text}\n\n"
                f"Provide a single 2-3 sentence professional summary of the key portfolio risks and observations. "
                f"Do NOT give financial advice. Be concise."
            )
            from app.external.openai_client import chat_query as openai_chat
            # Use a mock user context since this is system-level
            ai_summary = await openai_chat("PORTFOLIO", prompt, [])
            if ai_summary and "not configured" not in ai_summary:
                insights["ai_summary"] = ai_summary
                insights["ai_enriched"] = True
        except Exception:
            pass

    return insights
