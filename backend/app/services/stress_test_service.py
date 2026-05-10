"""Stress testing and scenario analysis for portfolio risk.

Simulates how the portfolio would perform under various market scenarios
using historical betas and current holdings data.
"""
from typing import Any, Dict, List, Optional, Tuple

from app.services import market_data_service
from app.services.risk_service import _build_weighted_returns, get_risk_summary


# ── Stress scenarios ─────────────────────────────────────────────────────

SCENARIOS = [
    {
        "id": "nasdaq_crash",
        "name": "Nasdaq -5% Selloff",
        "description": "A sudden 5% decline in the Nasdaq, typical of a risk-off event",
        "market_shock": -0.05,
        "volatility_shock": 0.30,
        "benchmark": "QQQ",
    },
    {
        "id": "rate_spike",
        "name": "Treasury Yield Spike",
        "description": "10-year yields rise 50bps, pressuring growth and tech stocks",
        "market_shock": -0.03,
        "volatility_shock": 0.20,
        "benchmark": "SPY",
        "tech_penalty": 0.5,
    },
    {
        "id": "oil_shock",
        "name": "Oil Price Shock",
        "description": "Crude oil spikes 15% on supply concerns, impacting consumer sectors",
        "market_shock": -0.02,
        "volatility_shock": 0.25,
        "benchmark": "XLE",
    },
    {
        "id": "ai_correction",
        "name": "AI / Tech Sector Correction",
        "description": "AI-related stocks correct 10% as sentiment shifts",
        "market_shock": -0.10,
        "volatility_shock": 0.40,
        "benchmark": "QQQ",
        "tech_penalty": 1.5,
    },
    {
        "id": "recession",
        "name": "Broad Recession Scenario",
        "description": "Economic contraction with broad market decline and elevated volatility",
        "market_shock": -0.15,
        "volatility_shock": 0.50,
        "benchmark": "SPY",
    },
]


async def run_stress_tests(holdings_data: List[Dict]) -> Dict[str, Any]:
    """Run all predefined stress scenarios against the portfolio.

    Returns impact estimates under each scenario based on historical beta
    and current portfolio composition.
    """
    ret, pv, symbols = await _build_weighted_returns(holdings_data)
    if ret is None or pv <= 0:
        return {"error": "Insufficient data for stress testing", "scenarios": []}

    total_value = pv
    results = []
    worst_impact = 0.0
    worst_scenario = None

    for scenario in SCENARIOS:
        impact = await _simulate_scenario(holdings_data, total_value, scenario, symbols)
        results.append(impact)
        if impact["impact_pct"] < worst_impact:
            worst_impact = impact["impact_pct"]
            worst_scenario = scenario["name"]

    return {
        "scenarios": results,
        "worst_case": {"scenario": worst_scenario, "impact_pct": round(worst_impact, 2)} if worst_scenario else None,
        "portfolio_value": round(total_value, 2),
    }


async def _simulate_scenario(
    holdings_data: List[Dict], total_value: float, scenario: Dict, symbols_in_portfolio: List[str]
) -> Dict[str, Any]:
    """Simulate a single scenario against each holding."""
    impacts = []
    total_impact_value = 0.0
    is_tech_penalty = "tech_penalty" in scenario

    for h in holdings_data:
        mv = float(h.get("market_value", 0) or 0)
        if mv <= 0:
            continue

        weight = mv / total_value if total_value > 0 else 0
        symbol = h["symbol"]

        # Try to get beta for this position
        beta = 1.0
        try:
            info = await market_data_service.get_info(symbol)
            if isinstance(info, dict):
                b = info.get("beta")
                if b is not None:
                    beta = float(b)
        except Exception:
            pass

        # Check if tech stock (for tech penalty scenarios)
        sector = ""
        try:
            info = await market_data_service.get_info(symbol)
            if isinstance(info, dict):
                sector = info.get("sector", "") or ""
        except Exception:
            pass

        is_tech = "technology" in sector.lower() or "semiconductor" in sector.lower()

        # Calculate scenario impact
        shock = scenario["market_shock"]
        if is_tech and is_tech_penalty:
            shock *= (1 + scenario.get("tech_penalty", 0))

        position_impact = shock * beta * mv
        total_impact_value += position_impact

        impacts.append({
            "symbol": symbol,
            "impact_value": round(position_impact, 2),
            "impact_pct": round(shock * beta * 100, 2),
            "beta_used": round(beta, 2),
        })

    impacts.sort(key=lambda x: x["impact_value"])
    total_impact_pct = total_impact_value / total_value * 100 if total_value > 0 else 0

    return {
        "scenario_id": scenario["id"],
        "scenario_name": scenario["name"],
        "description": scenario["description"],
        "market_shock_pct": round(scenario["market_shock"] * 100, 1),
        "volatility_shock_pct": round(scenario["volatility_shock"] * 100, 1),
        "impact_pct": round(total_impact_pct, 2),
        "impact_value": round(total_impact_value, 2),
        "position_impacts": impacts[:5],
    }
