from typing import Optional
import numpy as np
import pandas as pd

from app.schemas.portfolio import PerformanceResponse

MIN_DATA_POINTS = 20  # Minimum trading days to compute annualized metrics


def _compute_metrics(returns: np.ndarray, risk_free_rate: float = 0.05) -> PerformanceResponse:
    """Compute performance metrics from a daily return series.

    Args:
        returns: Array of daily returns (e.g. 0.01 for 1%).
        risk_free_rate: Annual risk-free rate (default 5%).

    Returns:
        PerformanceResponse with computed values, or all-None if too little data.
    """
    if len(returns) < 2:
        return PerformanceResponse()

    n_days = len(returns)
    avg_return = float(returns.mean())
    std_return = float(returns.std())

    # Total return: compound growth over the full period
    total_return = float(np.prod(1 + returns) - 1)

    # Annualized metrics — only if we have enough data
    # Multiply daily avg return by 252 (trading days/year) to annualize
    if n_days >= MIN_DATA_POINTS:
        annualized_return = avg_return * 252.0
        volatility = std_return * np.sqrt(252.0) if std_return > 1e-10 else None
        sharpe = None
        if volatility is not None and volatility > 1e-10:
            sharpe = (annualized_return - risk_free_rate) / volatility
    else:
        annualized_return = None
        volatility = None
        sharpe = None

    # Max drawdown from cumulative returns
    cum_returns = np.cumprod(1 + returns)
    running_max = np.maximum.accumulate(cum_returns)
    drawdown_series = (cum_returns - running_max) / running_max
    max_drawdown = float(drawdown_series.min()) if len(drawdown_series) > 0 else None

    return PerformanceResponse(
        total_return_pct=None if total_return is None else round(total_return * 100, 2),
        annualized_return_pct=None if annualized_return is None else round(annualized_return * 100, 2),
        volatility_pct=None if volatility is None else round(volatility * 100, 2),
        sharpe_ratio=None if sharpe is None else round(sharpe, 4),
        max_drawdown_pct=None if max_drawdown is None else round(max_drawdown * 100, 2),
    )


def calculate_performance_from_prices(prices: list[float], **kwargs) -> PerformanceResponse:
    """Calculate performance from a single price series (single-holding portfolios)."""
    if len(prices) < 2:
        return PerformanceResponse()
    returns = pd.Series(prices).pct_change().dropna().values
    if len(returns) < 1:
        return PerformanceResponse()
    return _compute_metrics(returns, **kwargs)


def calculate_performance_from_weighted_returns(
    holding_histories: list[list[float]],
    weights: list[float],
    **kwargs,
) -> PerformanceResponse:
    """Calculate portfolio performance from weighted holding returns.

    Aligns all return series to the same length (shortest), computes a
    weighted portfolio daily return series, then derives all metrics.
    """
    return_series = []
    active_weights = []
    for prices, w in zip(holding_histories, weights):
        if len(prices) < 2:
            continue
        r = pd.Series(prices).pct_change().dropna().values
        if len(r) < 2:
            continue
        return_series.append(r)
        active_weights.append(w)

    total_w = sum(active_weights)
    if not return_series or total_w <= 0:
        return PerformanceResponse()

    # Align to shortest common length
    min_len = min(len(r) for r in return_series)
    norm_weights = np.array(active_weights) / total_w

    portfolio_returns = sum(w * r[-min_len:] for w, r in zip(norm_weights, return_series))
    return _compute_metrics(portfolio_returns, **kwargs)
