"""Institutional-quality risk analytics using weighted portfolio returns.

Every function uses the same portfolio return series computed from holdings
price histories, weighted by current market value.  This ensures consistency
across VaR, Beta, drawdown, and correlation calculations.
"""
from decimal import Decimal
from typing import Any, Dict, List, Optional, Tuple
import numpy as np
import pandas as pd
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.risk_calculation import RiskCalculation
from app.services import market_data_service

# ── Helpers ──────────────────────────────────────────────────────────────

MIN_DATA_POINTS = 20  # trading days needed for meaningful annualized metrics


def _safe_float(v: Any) -> float:
    """Coerce to float.  NaN / Inf → 0.0."""
    try:
        x = float(v)
        return x if np.isfinite(x) else 0.0
    except (TypeError, ValueError):
        return 0.0


async def _build_weighted_returns(
    holdings_data: List[Dict],
    lookback_days: int = 252,
) -> Tuple[Optional[np.ndarray], float, List[str]]:
    """Build a single weighted portfolio daily return series from holdings.

    Returns (portfolio_returns, portfolio_value, symbols_used) or
    (None, 0, []) if insufficient data.
    """
    all_returns: List[np.ndarray] = []
    weights: List[float] = []
    symbols: List[str] = []
    total_value = 0.0

    for h in holdings_data:
        history = await market_data_service.get_history(h["symbol"], "1d", "1y")
        if not history or len(history) < MIN_DATA_POINTS:
            continue
        prices = [p["close"] for p in history[-lookback_days:]]
        returns = pd.Series(prices).pct_change().dropna().values
        if len(returns) < MIN_DATA_POINTS:
            continue
        mv = _safe_float(h.get("market_value", 0))
        if mv <= 0:
            continue
        all_returns.append(returns)
        weights.append(mv)
        symbols.append(h["symbol"])
        total_value += mv

    if not all_returns or total_value <= 0:
        return None, 0.0, []

    # Align to shortest common length
    min_len = min(len(r) for r in all_returns)
    norm_weights = np.array(weights) / total_value

    portfolio_returns = sum(w * r[-min_len:] for w, r in zip(norm_weights, all_returns))
    return portfolio_returns, total_value, symbols


# ── Consolidated risk summary ────────────────────────────────────────────


async def get_risk_summary(holdings_data: List[Dict]) -> Dict[str, Any]:
    """Compute all risk metrics in one pass and return a single dict.

    Returns a structure suitable for the frontend risk dashboard.
    """
    ret, pv, symbols = await _build_weighted_returns(holdings_data)
    if ret is None:
        return {"error": "Insufficient historical price data", "data_available": False}

    n = len(ret)
    avg_ret = float(ret.mean())
    std_ret = float(ret.std())

    # Annualized volatility
    vol = std_ret * np.sqrt(252) if std_ret > 1e-10 else 0.0

    # Sharpe ratio (assuming 5% risk-free rate)
    sharpe = ((avg_ret * 252) - 0.05) / vol if vol > 1e-10 else None

    # Max drawdown
    cum = np.cumprod(1 + ret)
    running_max = np.maximum.accumulate(cum)
    dd_series = (cum - running_max) / running_max
    max_dd = float(dd_series.min())
    current_dd = float(dd_series[-1])
    max_dd_idx = int(np.argmin(dd_series))

    # VaR and CVaR (historical simulation)
    var_95 = float(np.percentile(ret, 5))
    cvar_95 = float(ret[ret <= var_95].mean()) if len(ret[ret <= var_95]) > 0 else var_95
    var_99 = float(np.percentile(ret, 1))
    cvar_99 = float(ret[ret <= var_99].mean()) if len(ret[ret <= var_99]) > 0 else var_99

    # Beta vs SPY
    beta_result = await _calc_beta(ret)

    # Sector & top position concentration
    concentration = await _calc_concentration(holdings_data, symbols)

    return {
        "data_available": True,
        "n_days": n,
        "portfolio_value": round(pv, 2),
        "volatility": {
            "daily": round(float(ret.std()) * 100, 2),
            "annualized": round(vol * 100, 2) if vol > 0 else None,
        },
        "sharpe_ratio": round(sharpe, 4) if sharpe is not None else None,
        "drawdown": {
            "max_pct": round(max_dd * 100, 2),
            "current_pct": round(current_dd * 100, 2),
            "max_drawdown_date_idx": max_dd_idx,
        },
        "value_at_risk": {
            "var_95_pct": round(var_95 * 100, 2),
            "cvar_95_pct": round(cvar_95 * 100, 2),
            "var_95_value": round(pv * var_95, 2),
            "cvar_95_value": round(pv * cvar_95, 2),
            "var_99_pct": round(var_99 * 100, 2),
            "cvar_99_pct": round(cvar_99 * 100, 2),
        },
        "beta": beta_result,
        "concentration": concentration,
    }


async def _calc_beta(portfolio_returns: np.ndarray) -> Dict[str, Any]:
    """Beta vs SPY using the same date-aligned return series."""
    bench_history = await market_data_service.get_history("SPY", "1d", "1y")
    if not bench_history or len(bench_history) < MIN_DATA_POINTS:
        return {"error": "Insufficient SPY data"}

    bench_prices = [p["close"] for p in bench_history]
    bench_returns = pd.Series(bench_prices).pct_change().dropna().values

    min_len = min(len(portfolio_returns), len(bench_returns))
    pr = portfolio_returns[-min_len:]
    br = bench_returns[-min_len:]

    cov = np.cov(pr, br)[0, 1]
    market_var = np.var(br)
    if market_var <= 1e-10:
        return {"error": "Benchmark variance too small"}

    b = cov / market_var
    corr = np.corrcoef(pr, br)[0, 1] if len(pr) > 1 else 0.0
    alpha = (float(pr.mean()) - b * float(br.mean())) * 252
    r2 = corr ** 2

    return {
        "beta": round(float(b), 4),
        "alpha": round(alpha, 4),
        "correlation": round(float(corr), 4),
        "r_squared": round(float(r2), 4),
        "benchmark": "SPY",
        "n_days": min_len,
    }


async def _calc_concentration(
    holdings_data: List[Dict],
    symbols_in_returns: List[str],
) -> Dict[str, Any]:
    """Top holdings concentration and sector exposure."""
    total = sum(_safe_float(h.get("market_value", 0)) for h in holdings_data)
    if total <= 0:
        return {"error": "No positive-value holdings"}

    holdings_with_value = [
        {"symbol": h["symbol"], "value": _safe_float(h.get("market_value", 0)), "pct": _safe_float(h.get("market_value", 0)) / total * 100}
        for h in holdings_data
    ]
    holdings_with_value.sort(key=lambda x: x["value"], reverse=True)

    # Top holdings
    top = holdings_with_value[:5]

    # Herfindahl-Hirschman Index (sum of squared weights * 10000)
    weights = np.array([h["pct"] / 100 for h in holdings_with_value])
    hhi = int(np.sum(weights ** 2) * 10000)

    # Sector data (best-effort from yfinance)
    sector_map: Dict[str, float] = {}
    sector_errors = 0
    for h in holdings_with_value:
        try:
            info = await market_data_service.get_info(h["symbol"])
            sector = info.get("sector") if isinstance(info, dict) else None
            if sector:
                sector_map[sector] = sector_map.get(sector, 0) + h["pct"]
            else:
                sector_errors += 1
        except Exception:
            sector_errors += 1

    return {
        "total_value": round(total, 2),
        "top_holdings": top,
        "hhi": hhi,
        "sectors": sector_map if sector_map else None,
        "sectors_unavailable": sector_errors > 0 and not sector_map,
    }


# ── Correlation matrix ───────────────────────────────────────────────────


async def get_correlation_matrix(holdings_data: List[Dict]) -> Dict[str, Any]:
    """Pairwise correlation of holding returns over the past year."""
    symbol_returns: Dict[str, np.ndarray] = {}
    for h in holdings_data:
        history = await market_data_service.get_history(h["symbol"], "1d", "1y")
        if not history or len(history) < MIN_DATA_POINTS:
            continue
        prices = [p["close"] for p in history]
        r = pd.Series(prices).pct_change().dropna().values
        if len(r) >= MIN_DATA_POINTS:
            symbol_returns[h["symbol"]] = r

    symbols = list(symbol_returns.keys())
    if len(symbols) < 2:
        return {"error": "Need at least 2 holdings with sufficient history", "symbols": symbols}

    # Align to shortest
    min_len = min(len(symbol_returns[s]) for s in symbols)
    arr = np.column_stack([symbol_returns[s][-min_len:] for s in symbols])
    corr = np.corrcoef(arr.T)

    return {
        "symbols": symbols,
        "matrix": [[round(float(v), 4) for v in row] for row in corr.tolist()],
        "n_days": min_len,
    }


# ── Legacy individual-calc endpoints (kept for backward compat) ────────────


async def calculate_var(holdings_data: List[Dict], confidence: float = 0.95) -> Dict[str, Any]:
    summary = await get_risk_summary(holdings_data)
    if "error" in summary:
        return summary
    var = summary["value_at_risk"]
    key = "var_95" if confidence >= 0.94 else "var_99"
    return {
        "confidence_level": confidence,
        "var_pct": var[f"{key}_pct"],
        "var_value": var[f"{key}_value"],
        "cvar_pct": var[f"cvar_{key.split('_')[1]}_pct"],
        "cvar_value": var[f"cvar_{key.split('_')[1]}_value"],
        "portfolio_value": summary["portfolio_value"],
    }


async def calculate_beta(holdings_data: List[Dict], benchmark: str = "SPY") -> Dict[str, Any]:
    ret, pv, _ = await _build_weighted_returns(holdings_data)
    if ret is None:
        return {"error": "Insufficient data for Beta calculation"}
    return await _calc_beta(ret)


async def calculate_drawdown(holdings_data: List[Dict]) -> Dict[str, Any]:
    summary = await get_risk_summary(holdings_data)
    if "error" in summary:
        return summary
    return summary["drawdown"]


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
