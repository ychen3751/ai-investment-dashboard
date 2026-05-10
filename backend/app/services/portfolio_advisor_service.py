"""Institutional-grade portfolio advisor — analyzes holdings, risk, concentration,
sector exposure, and correlation to generate actionable insights.

Fully deterministic.  Optional OpenAI for natural-language summary.
Never gives financial advice.
"""
from decimal import Decimal
from typing import Any, Dict, List, Optional
import numpy as np

from app.core.config import settings
from app.services import market_data_service, risk_service
from app.services.performance_service import calculate_performance_from_weighted_returns


async def get_advisor_analysis(holdings_data: List[Dict]) -> Dict[str, Any]:
    """Full portfolio advisor analysis.

    holdings_data: list of dicts with symbol, market_value, total_cost, total_pnl, total_pnl_pct
    """
    if not holdings_data:
        return _empty_response("Add holdings to get portfolio analysis.")

    # Compute derived values
    total_value = sum(float(h.get("market_value", 0) or 0) for h in holdings_data)
    total_cost = sum(float(h.get("total_cost", 0) or 0) for h in holdings_data)
    n = len(holdings_data)

    if total_value <= 0:
        return _empty_response("Portfolio has no positive-value holdings.")

    # ── Weights & top holdings ─────────────────────────────────────────
    for h in holdings_data:
        mv = float(h.get("market_value", 0) or 0)
        h["weight"] = round(mv / total_value * 100, 2) if total_value > 0 else 0

    sorted_holdings = sorted(holdings_data, key=lambda x: x.get("weight", 0), reverse=True)

    # ── Concentration metrics ──────────────────────────────────────────
    weights = np.array([h["weight"] / 100 for h in sorted_holdings])
    hhi = int(np.sum(weights ** 2) * 10000)
    top_weight = sorted_holdings[0]["weight"] if sorted_holdings else 0
    top3_weight = sum(h["weight"] for h in sorted_holdings[:3]) if len(sorted_holdings) >= 3 else sum(h["weight"] for h in sorted_holdings)

    # ── Sector exposure ────────────────────────────────────────────────
    sectors: Dict[str, float] = {}
    for h in sorted_holdings:
        try:
            info = await market_data_service.get_info(h["symbol"])
            sector = info.get("sector") if isinstance(info, dict) else None
            if sector:
                sectors[sector] = sectors.get(sector, 0) + h["weight"]
        except Exception:
            pass

    sector_exposure = [{"sector": k, "weight": round(v, 1)} for k, v in sorted(sectors.items(), key=lambda x: -x[1])]

    # ── Risk metrics (from risk service) ───────────────────────────────
    risk = {}
    try:
        risk_summary = await risk_service.get_risk_summary(holdings_data)
        if "error" not in risk_summary:
            risk = {
                "volatility_annualized": risk_summary.get("volatility", {}).get("annualized"),
                "sharpe_ratio": risk_summary.get("sharpe_ratio"),
                "max_drawdown": risk_summary.get("drawdown", {}).get("max_pct"),
                "current_drawdown": risk_summary.get("drawdown", {}).get("current_pct"),
                "beta": risk_summary.get("beta", {}).get("beta") if isinstance(risk_summary.get("beta"), dict) else None,
                "correlation": risk_summary.get("beta", {}).get("correlation") if isinstance(risk_summary.get("beta"), dict) else None,
                "var_95": risk_summary.get("value_at_risk", {}).get("var_95_pct"),
            }
    except Exception:
        pass

    # ── Correlation (if ≥2 holdings) ───────────────────────────────────
    corr_data = None
    if n >= 2:
        try:
            corr = await risk_service.get_correlation_matrix(holdings_data)
            if "error" not in corr:
                symbols = corr.get("symbols", [])
                matrix = corr.get("matrix", [])
                corr_data = {"symbols": symbols, "matrix": matrix}
        except Exception:
            pass

    # ── Performance attribution ────────────────────────────────────────
    sorted_by_pnl = sorted(holdings_data, key=lambda x: float(x.get("total_pnl_pct", 0) or 0), reverse=True)
    top_contributors = [
        {"symbol": h["symbol"], "pnl_pct": round(float(h.get("total_pnl_pct", 0) or 0), 2), "weight": h["weight"]}
        for h in sorted_by_pnl[:5]
    ]

    # ── Scoring ────────────────────────────────────────────────────────
    div_score = _diversification_score(hhi, n, top_weight, top3_weight)
    conc_score = max(0, 100 - div_score)
    beta = risk.get("beta")

    if beta is not None and beta > 0:
        beta_score = max(0, min(100, 50 - (beta - 1) * 30))
    else:
        beta_score = 50

    risk_score = round((100 - div_score) * 0.5 + (100 - beta_score) * 0.3 + (conc_score) * 0.2, 1)
    portfolio_score = round((div_score * 0.4 + beta_score * 0.3 + max(0, 100 - risk_score) * 0.3), 1)

    # ── Top risks ──────────────────────────────────────────────────────
    top_risks = _top_risks(n, top_weight, top3_weight, hhi, sector_exposure, beta, risk)

    # ── Suggestions ────────────────────────────────────────────────────
    suggestions = _suggestions(n, top_weight, hhi, beta, sector_exposure, risk)

    # ── Correlation analysis ───────────────────────────────────────────
    corr_analysis = _correlation_analysis(corr_data, holdings_data)

    # ── AI Summary ─────────────────────────────────────────────────────
    ai_summary = _generate_advisor_summary(portfolio_score, risk_score, div_score, beta, n, top_weight, sector_exposure, top_risks)

    # Optional OpenAI
    ai_narrative = None
    if settings.OPENAI_API_KEY and settings.OPENAI_API_KEY != "placeholder_openai_api_key":
        try:
            prompt = (
                f"Portfolio: score={portfolio_score}, risk={risk_score}, diversification={div_score}, "
                f"holdings={n}, beta={beta}, sectors={[s['sector'] for s in sector_exposure[:3]]}. "
                f"Write 2-3 sentences of portfolio analysis. Do NOT give financial advice."
            )
            from app.external.openai_client import chat_query as openai_chat
            result = await openai_chat("PORTFOLIO", prompt, [])
            if result and "not configured" not in result:
                ai_narrative = result
        except Exception:
            pass

    # ── Beginner explanation ───────────────────────────────────────────
    beginner = _beginner_explanation(portfolio_score, n, top_weight, beta, sector_exposure)

    return {
        "portfolio_score": portfolio_score,
        "risk_score": risk_score,
        "diversification_score": div_score,
        "market_beta": beta,
        "sector_exposure": sector_exposure,
        "top_contributors": top_contributors,
        "top_risks": top_risks,
        "correlation_analysis": corr_analysis,
        "risk_metrics": risk,
        "portfolio_health": {
            "holdings_count": n,
            "total_value": round(total_value, 2),
            "total_cost": round(total_cost, 2),
            "top_holding_weight": top_weight,
            "top3_holding_weight": top3_weight,
            "hhi": hhi,
        },
        "ai_summary": ai_narrative or ai_summary,
        "beginner_explanation": beginner,
        "suggestions": suggestions,
    }


def _diversification_score(hhi: int, n: int, top_weight: float, top3_weight: float) -> float:
    if n <= 1:
        return 10
    if n <= 3:
        return max(10, 50 - top_weight * 0.5)
    hhi_score = max(0, 100 - hhi / 50)
    count_score = min(100, n * 10)
    top_score = max(0, 100 - top_weight * 1.5) if top_weight > 20 else 100
    return round((hhi_score * 0.4 + count_score * 0.3 + top_score * 0.3), 1)


def _top_risks(n, top_weight, top3_weight, hhi, sector_exposure, beta, risk) -> List[Dict]:
    risks = []
    if n <= 3:
        risks.append({"risk": "Concentration Risk", "detail": f"Only {n} holdings — portfolio lacks diversification", "severity": "high"})
    if top_weight > 30:
        risks.append({"risk": "Single-Stock Concentration", "detail": f"Top holding is {top_weight:.1f}% of portfolio", "severity": "high"})
    if top3_weight > 70:
        risks.append({"risk": "Top-Heavy Portfolio", "detail": f"Top 3 holdings represent {top3_weight:.1f}% of portfolio", "severity": "medium"})
    if len(sector_exposure) <= 2:
        sectors_str = ", ".join(s["sector"] for s in sector_exposure)
        risks.append({"risk": "Sector Concentration", "detail": f"Portfolio concentrated in {len(sector_exposure)} sector(s): {sectors_str}", "severity": "high"})
    if beta is not None and beta > 1.3:
        risks.append({"risk": "High Beta", "detail": f"Beta of {beta:.2f} — portfolio amplifies market moves by {((beta - 1) * 100):.0f}%", "severity": "medium"})
    if risk.get("max_drawdown") is not None and risk["max_drawdown"] < -30:
        risks.append({"risk": "High Drawdown Risk", "detail": f"Historical max drawdown of {risk['max_drawdown']:.1f}%", "severity": "medium"})
    return risks


def _suggestions(n, top_weight, hhi, beta, sector_exposure, risk) -> List[str]:
    s = []
    if n <= 5:
        s.append("Consider adding 3-5 uncorrelated positions to improve diversification")
    if top_weight > 25:
        s.append(f"Top holding is {top_weight:.1f}% of portfolio — consider trimming to reduce single-stock risk")
    if len(sector_exposure) <= 2:
        covered = ", ".join(s["sector"] for s in sector_exposure)
        s.append(f"Portfolio is concentrated in {covered}. Consider adding exposure to defensive sectors (utilities, healthcare, consumer staples)")
    if beta is not None and beta > 1.3:
        s.append(f"Beta of {beta:.2f} is elevated — adding bonds or low-beta equities could reduce volatility")
    if risk.get("max_drawdown") is not None and risk["max_drawdown"] < -25:
        s.append("Consider implementing stop-losses or hedging strategies to manage drawdown risk")
    if not s:
        s.append("Portfolio appears well-diversified. Continue monitoring and rebalancing periodically.")
    return s


def _correlation_analysis(corr_data, holdings_data) -> Dict[str, Any]:
    if not corr_data or len(corr_data.get("symbols", [])) < 2:
        return {"available": False, "message": "Need at least 2 holdings for correlation analysis."}
    symbols = corr_data["symbols"]
    matrix = corr_data["matrix"]
    avg_corr = None
    off_diag = []
    for i in range(len(symbols)):
        for j in range(len(symbols)):
            if i < j and i < len(matrix) and j < len(matrix[i]):
                off_diag.append(abs(matrix[i][j]))
    if off_diag:
        avg_corr = round(np.mean(off_diag), 4)
    pairs = []
    for i in range(len(symbols)):
        for j in range(len(symbols)):
            if i < j and i < len(matrix) and j < len(matrix[i]):
                pairs.append({"pair": f"{symbols[i]}/{symbols[j]}", "correlation": round(matrix[i][j], 4)})
    pairs.sort(key=lambda x: abs(x["correlation"]), reverse=True)
    return {"available": True, "symbols": symbols, "matrix": matrix, "average_correlation": avg_corr, "pairs": pairs[:5]}


def _generate_advisor_summary(score, risk, div, beta, n, top_weight, sectors, risks) -> str:
    score_label = "strong" if score >= 70 else "moderate" if score >= 50 else "needs improvement"
    parts = [f"Portfolio scores {score}/100 ({score_label})."]
    if beta is not None:
        parts.append(f"Beta of {beta:.2f} indicates {'above-market' if beta > 1.1 else 'market-line' if beta > 0.9 else 'below-market'} volatility.")
    parts.append(f"Diversification is {'good' if div >= 60 else 'moderate' if div >= 40 else 'low'} ({div}/100).")
    if sectors:
        parts.append(f"Primary exposure: {sectors[0]['sector']} ({sectors[0]['weight']}%).")
    if len(risks) > 0:
        parts.append(f"Top risk: {risks[0]['risk']}.")
    return " ".join(parts)


def _beginner_explanation(score: float, n: int, top_weight: float, beta: Optional[float], sectors: List[Dict]) -> str:
    lines = []
    if n <= 2:
        lines.append("Your portfolio has very few holdings, which means it's highly dependent on the performance of each individual stock. Adding more positions could reduce risk.")
    elif n <= 5:
        lines.append(f"Your portfolio has {n} holdings — a reasonable starting point, but additional positions could improve diversification.")
    else:
        lines.append(f"With {n} holdings, your portfolio has a solid foundation for diversification.")
    if top_weight > 30:
        lines.append(f"The largest position makes up {top_weight:.1f}% of your portfolio — if that stock declines significantly, it will have a large impact.")
    if beta is not None:
        if beta > 1.3:
            lines.append(f"Your portfolio's beta of {beta:.2f} means it tends to move more than the overall market — both up and down.")
        elif beta < 0.8:
            lines.append(f"Your portfolio's beta of {beta:.2f} means it tends to be more stable than the overall market.")
        else:
            lines.append(f"Your portfolio's beta of {beta:.2f} suggests it moves broadly in line with the market.")
    return " ".join(lines)


def _empty_response(message: str) -> Dict[str, Any]:
    return {
        "portfolio_score": 0, "risk_score": 0, "diversification_score": 0, "market_beta": None,
        "sector_exposure": [], "top_contributors": [], "top_risks": [],
        "correlation_analysis": {"available": False, "message": "Insufficient data."},
        "risk_metrics": {}, "portfolio_health": {},
        "ai_summary": message, "beginner_explanation": message, "suggestions": [],
    }
