"""Earnings analysis engine — evaluates upcoming earnings setups using
historical data, price momentum, and options market signals.

Deterministic fallback always works.  Optional OpenAI enrichment generates
a professional narrative.  Never gives buy/sell advice.
"""
from datetime import date, datetime
from typing import Any, Dict, List, Optional
import numpy as np

from app.core.config import settings
from app.external import yahoo_finance
from app.services import market_data_service
from app.services.technical_service import sma


async def get_earnings_analysis(symbol: str) -> Dict[str, Any]:
    """Full earnings setup analysis for a symbol."""
    info = await yahoo_finance.get_info(symbol)
    if not info:
        return {"symbol": symbol.upper(), "overall_signal": "neutral", "confidence": 0, "summary": "Data unavailable for this symbol."}

    company = info.get("shortName") or info.get("longName") or symbol
    history = await market_data_service.get_history(symbol, "1d", "6mo")
    closes = [p["close"] for p in history] if history else []

    # ── EPS Surprise History ───────────────────────────────────────────
    earnings_data = info.get("earningsData", {}) if isinstance(info.get("earningsData"), dict) else {}
    earnings_list = earnings_data.get("earningsList", []) if isinstance(earnings_data.get("earningsList"), list) else []

    surprises: List[float] = []
    for entry in earnings_list[:8]:
        if isinstance(entry, dict):
            actual = entry.get("epsActual")
            estimate = entry.get("epsEstimate")
            if actual and estimate and float(estimate) != 0:
                surprises.append((float(actual) - float(estimate)) / abs(float(estimate)) * 100)

    positive_surprises = sum(1 for s in surprises if s > 0)
    avg_surprise = np.mean(surprises) if surprises else None
    surprise_count = len(surprises)

    # ── Revenue Growth ─────────────────────────────────────────────────
    revenue = info.get("totalRevenue")
    prev_revenue = info.get("revenueQuarterlyPrevious") or info.get("lastFiscalYearRevenue")
    revenue_growth = None
    if revenue and prev_revenue and float(prev_revenue) > 0:
        revenue_growth = (float(revenue) - float(prev_revenue)) / float(prev_revenue) * 100

    # ── Price Momentum ─────────────────────────────────────────────────
    current_price = info.get("currentPrice") or info.get("regularMarketPrice") or 0
    momentum = {}
    if len(closes) >= 50:
        sma20_vals = sma(closes, 20)
        sma50_vals = sma(closes, 50)
        last_price = closes[-1]
        above_sma20 = last_price > (sma20_vals[-1] or 0)
        above_sma50 = last_price > (sma50_vals[-1] or 0)
        momentum = {"above_sma20": above_sma20, "above_sma50": above_sma50, "price": last_price}
        # Run-up in last 20 days
        if len(closes) >= 20:
            run_up = (closes[-1] - closes[-21]) / closes[-21] * 100
            momentum["run_up_pct"] = round(run_up, 2)
        else:
            momentum["run_up_pct"] = 0
    elif len(closes) >= 20:
        run_up = (closes[-1] - closes[-20]) / closes[-20] * 100 if len(closes) >= 20 else 0
        momentum = {"above_sma20": None, "above_sma50": None, "price": closes[-1] if closes else 0, "run_up_pct": round(run_up, 2)}
    else:
        momentum = {"above_sma20": None, "above_sma50": None, "price": current_price, "run_up_pct": None}

    # ── Valuation ──────────────────────────────────────────────────────
    pe = info.get("trailingPE")
    forward_pe = info.get("forwardPE")
    sector_pe = info.get("sectorPE")
    valuation_note = None
    if pe and forward_pe:
        if pe > 30 and forward_pe > 25:
            valuation_note = "elevated"
        elif pe < 15:
            valuation_note = "low"
        else:
            valuation_note = "moderate"

    # ── IV / Options Risk ──────────────────────────────────────────────
    iv_risk = None
    try:
        chain = await yahoo_finance.get_options_chain(symbol)
        if chain:
            all_ivs = []
            for opt_type in ("calls", "puts"):
                for c in chain.get(opt_type, []):
                    iv = c.get("implied_volatility", 0) or 0
                    if iv > 0:
                        all_ivs.append(iv * 100)
            if all_ivs:
                avg_iv = np.mean(all_ivs)
                if avg_iv > 60:
                    iv_risk = "high"
                elif avg_iv > 35:
                    iv_risk = "moderate"
                else:
                    iv_risk = "low"
    except Exception:
        pass

    # ── Build factors ──────────────────────────────────────────────────
    bullish: List[str] = []
    bearish: List[str] = []
    risk: List[str] = []

    # EPS surprise history
    if surprise_count >= 4:
        if avg_surprise and avg_surprise > 3:
            bullish.append(f"Consistent EPS beats — {positive_surprises}/{surprise_count} quarters beat estimates (avg +{avg_surprise:.1f}%)")
        elif avg_surprise and avg_surprise < -3:
            bearish.append(f"Recent EPS misses — only {positive_surprises}/{surprise_count} quarters beat estimates")
    elif surprise_count > 0:
        if avg_surprise and avg_surprise > 0:
            bullish.append(f"Positive EPS surprise trend ({avg_surprise:.1f}% avg beat)")
        elif avg_surprise and avg_surprise < 0:
            bearish.append(f"Negative EPS surprise trend ({avg_surprise:.1f}% avg miss)")

    # Revenue growth
    if revenue_growth is not None:
        if revenue_growth > 10:
            bullish.append(f"Revenue growth accelerating ({revenue_growth:.1f}% YoY)")
        elif revenue_growth > 5:
            bullish.append(f"Moderate revenue growth ({revenue_growth:.1f}% YoY)")
        elif revenue_growth < 0:
            bearish.append(f"Revenue declining ({revenue_growth:.1f}% YoY)")

    # Price momentum
    if momentum.get("above_sma20") and momentum.get("above_sma50"):
        bullish.append(f"Price above both 20 and 50-day moving averages — bullish momentum heading into earnings")
    elif momentum.get("above_sma20"):
        bullish.append("Price above 20-day moving average — short-term momentum positive")

    if momentum.get("run_up_pct") is not None:
        if momentum["run_up_pct"] > 15:
            risk.append(f"Significant pre-earnings run-up ({momentum['run_up_pct']:.1f}%) — risk of post-earnings selloff")
        elif momentum["run_up_pct"] > 8:
            risk.append(f"Moderate pre-earnings rally ({momentum['run_up_pct']:.1f}%) — some gains may be priced in")

    # Valuation risk
    if valuation_note == "elevated":
        risk.append(f"Elevated valuation (P/E {pe:.1f}, forward {forward_pe:.1f}) — high expectations already priced in")
    elif valuation_note == "low":
        bullish.append(f"Moderate valuation (P/E {pe:.1f}) — room for positive surprise")

    # IV risk
    if iv_risk == "high":
        risk.append(f"Elevated implied volatility before earnings — options market pricing large move; IV crush risk post-report")
    elif iv_risk == "moderate":
        risk.append("Moderate implied volatility — options market expecting a normal-sized move")

    # ── Determine signal ───────────────────────────────────────────────
    b_score = len(bullish)
    be_score = len(bearish)
    r_score = len(risk)

    if iv_risk == "high" and (b_score == 0 or r_score >= 2):
        overall_signal = "high_risk"
        confidence = min(90, 50 + r_score * 12)
    elif b_score >= be_score + 2 and b_score >= 2:
        overall_signal = "bullish"
        confidence = min(90, 55 + b_score * 8 - be_score * 4)
    elif be_score >= b_score + 2 and be_score >= 2:
        overall_signal = "bearish"
        confidence = min(85, 50 + be_score * 8 - b_score * 4)
    elif b_score > 0 and be_score > 0:
        overall_signal = "mixed"
        confidence = 40 + (b_score + be_score) * 5
    else:
        overall_signal = "neutral"
        confidence = 25

    confidence = max(10, min(95, confidence))

    # ── Key signals ────────────────────────────────────────────────────
    key_signals = {
        "earnings_trend": f"{positive_surprises}/{surprise_count} quarters beat" if surprise_count > 0 else "Insufficient data",
        "eps_surprise_history": f"Avg {avg_surprise:+.1f}% surprise" if avg_surprise is not None else "N/A",
        "revenue_growth": f"{revenue_growth:+.1f}% YoY" if revenue_growth is not None else "N/A",
        "price_momentum": f"{'Above' if momentum.get('above_sma20') else 'Below'} 20-day MA" if momentum.get("above_sma20") is not None else "N/A",
        "options_iv_risk": f"{iv_risk.capitalize()} IV" if iv_risk else "N/A",
        "analyst_expectation": f"P/E {pe:.1f}" if pe else "N/A",
    }

    # ── Beginner explanation ───────────────────────────────────────────
    beginner = _beginner_explanation(overall_signal, company, bullish, bearish, risk)

    # ── Summary ────────────────────────────────────────────────────────
    summary = _generate_summary(overall_signal, company, surprise_count, avg_surprise, revenue_growth)

    # ── Optional OpenAI ────────────────────────────────────────────────
    ai_summary = None
    if settings.OPENAI_API_KEY and settings.OPENAI_API_KEY != "placeholder_openai_api_key":
        try:
            prompt = (
                f"Earnings analysis for {company} ({symbol}): signal={overall_signal}, confidence={confidence}. "
                f"Bullish: {bullish}. Bearish: {bearish}. Risk: {risk}. "
                f"Write 2-3 sentences. Do NOT give financial advice. Be concise."
            )
            from app.external.openai_client import chat_query as openai_chat
            ai_result = await openai_chat(symbol.upper(), prompt, [])
            if ai_result and "not configured" not in ai_result:
                ai_summary = ai_result
        except Exception:
            pass

    return {
        "symbol": symbol.upper(),
        "overall_signal": overall_signal,
        "confidence": confidence,
        "summary": summary,
        "ai_summary": ai_summary,
        "beginner_explanation": beginner,
        "bullish_factors": bullish,
        "bearish_factors": bearish,
        "risk_factors": risk,
        "key_signals": key_signals,
    }


def _beginner_explanation(signal: str, company: str, bullish: List[str], bearish: List[str], risk: List[str]) -> str:
    if signal == "bullish":
        base = f"The setup looks generally bullish for {company}. "
    elif signal == "bearish":
        base = f"The setup looks generally bearish for {company}. "
    elif signal == "high_risk":
        base = f"Earnings could be highly volatile for {company}. "
    elif signal == "mixed":
        base = f"The setup for {company} is mixed — there are both positive and negative signals. "
    else:
        base = f"The earnings setup for {company} is neutral — no strong directional signals. "

    if bullish:
        base += "Positive signals include: " + "; ".join(bullish[:2]) + ". "
    if bearish:
        base += "Concerns include: " + "; ".join(bearish[:2]) + ". "
    if risk:
        base += "Risks to watch: " + "; ".join(risk[:2]) + ". "

    base += "This is educational analysis — not financial advice. Past performance does not guarantee future results."
    return base


def _generate_summary(signal: str, company: str, surprise_count: int, avg_surprise: Optional[float], revenue_growth: Optional[float]) -> str:
    return f"{company} earnings setup appears {signal}."
