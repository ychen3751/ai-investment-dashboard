from decimal import Decimal
from typing import Any, Dict, List, Optional
import numpy as np
import pandas as pd
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.risk_calculation import RiskCalculation
from app.services import market_data_service


async def calculate_var(holdings_data: List[Dict], confidence: float = 0.95) -> Dict[str, Any]:
    """Calculate Value at Risk using historical simulation."""
    all_returns = []
    weights = []
    total_value = Decimal("0")

    for h in holdings_data:
        history = await market_data_service.get_history(h["symbol"], "1d", "1y")
        if history and len(history) > 20:
            prices = [p["close"] for p in history[-252:]]
            returns = pd.Series(prices).pct_change().dropna().tolist()
            all_returns.append(returns)
            weights.append(float(h.get("market_value", 0)))
            total_value += Decimal(str(h.get("market_value", 0)))

    if not all_returns or total_value == 0:
        return {"error": "Insufficient data for VaR calculation"}

    weights = np.array(weights) / sum(weights) if sum(weights) > 0 else np.ones(len(weights)) / len(weights)
    min_len = min(len(r) for r in all_returns)
    portfolio_returns = sum(w * np.array(r[-min_len:]) for w, r in zip(weights, all_returns))

    var = np.percentile(portfolio_returns, (1 - confidence) * 100)
    cvar = portfolio_returns[portfolio_returns <= var].mean() if len(portfolio_returns[portfolio_returns <= var]) > 0 else var

    return {
        "confidence_level": confidence,
        "var_pct": float(var) * 100,
        "var_value": float(total_value) * float(var),
        "cvar_pct": float(cvar) * 100,
        "cvar_value": float(total_value) * float(cvar),
        "portfolio_value": float(total_value),
    }


async def calculate_beta(holdings_data: List[Dict], benchmark: str = "SPY") -> Dict[str, Any]:
    """Calculate portfolio Beta vs benchmark."""
    portfolio_returns = None
    weights = []

    for h in holdings_data:
        history = await market_data_service.get_history(h["symbol"], "1d", "1y")
        if history and len(history) > 20:
            prices = [p["close"] for p in history[-252:]]
            returns = pd.Series(prices).pct_change().dropna().values
            if portfolio_returns is None:
                portfolio_returns = np.zeros_like(returns)
            portfolio_returns += returns * float(h.get("market_value", 0))
            weights.append(float(h.get("market_value", 0)))

    if portfolio_returns is None or sum(weights) == 0:
        return {"error": "Insufficient data for Beta calculation"}

    portfolio_returns = portfolio_returns / sum(weights)

    bench_history = await market_data_service.get_history(benchmark, "1d", "1y")
    if not bench_history or len(bench_history) < 20:
        return {"error": f"Insufficient data for {benchmark}"}

    bench_prices = [p["close"] for p in bench_history[-252:]]
    bench_returns = pd.Series(bench_prices).pct_change().dropna().values

    min_len = min(len(portfolio_returns), len(bench_returns))
    covariance = np.cov(portfolio_returns[:min_len], bench_returns[:min_len])[0, 1]
    market_variance = np.var(bench_returns[:min_len])
    beta = covariance / market_variance if market_variance > 0 else 1.0

    correlation = np.corrcoef(portfolio_returns[:min_len], bench_returns[:min_len])[0, 1]
    alpha_annual = (np.mean(portfolio_returns[:min_len]) - beta * np.mean(bench_returns[:min_len])) * 252
    r_squared = correlation ** 2

    return {
        "beta": round(float(beta), 4),
        "alpha": round(float(alpha_annual), 4),
        "correlation": round(float(correlation), 4),
        "r_squared": round(float(r_squared), 4),
        "benchmark": benchmark,
    }


async def calculate_drawdown(holdings_data: List[Dict]) -> Dict[str, Any]:
    """Calculate maximum drawdown and drawdown series."""
    combined_prices = None
    weights = []

    for h in holdings_data:
        history = await market_data_service.get_history(h["symbol"], "1d", "1y")
        if history and len(history) > 20:
            prices = np.array([p["close"] for p in history])
            if combined_prices is None:
                combined_prices = np.zeros_like(prices, dtype=float)
            combined_prices += prices * float(h.get("market_value", 0))
            weights.append(float(h.get("market_value", 0)))

    if combined_prices is None or sum(weights) == 0:
        return {"error": "Insufficient data for drawdown calculation"}

    combined_prices = combined_prices / sum(weights)
    running_max = np.maximum.accumulate(combined_prices)
    drawdown = (combined_prices - running_max) / running_max

    max_dd_idx = np.argmin(drawdown)
    max_dd = float(drawdown[max_dd_idx])
    recovery_idx = np.argmax(combined_prices[max_dd_idx:] >= running_max[max_dd_idx]) if max_dd_idx < len(combined_prices) - 1 else -1

    return {
        "max_drawdown_pct": round(max_dd * 100, 2),
        "max_drawdown_date": max_dd_idx,
        "recovery_days": int(recovery_idx) if recovery_idx > 0 else None,
        "current_drawdown_pct": round(float(drawdown[-1]) * 100, 2),
    }


async def save_calculation(db: AsyncSession, portfolio_id, calc_type: str, params: Dict, results: Dict):
    calc = RiskCalculation(
        portfolio_id=portfolio_id,
        calculation_type=calc_type,
        parameters=params,
        results=results,
    )
    db.add(calc)
    await db.flush()
    return calc
