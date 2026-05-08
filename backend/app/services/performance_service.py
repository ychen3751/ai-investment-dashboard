from decimal import Decimal
from typing import List, Optional
import numpy as np
import pandas as pd

from app.schemas.portfolio import PerformanceResponse


def calculate_performance(prices: List[float], risk_free_rate: float = 0.05) -> PerformanceResponse:
    if len(prices) < 2:
        return PerformanceResponse()

    series = pd.Series(prices)
    returns = series.pct_change().dropna()
    total_return = float((series.iloc[-1] - series.iloc[0]) / series.iloc[0])

    n_days = len(returns)
    annualization_factor = 252 / max(n_days, 1)

    avg_return = float(returns.mean())
    std_return = float(returns.std())

    annualized_return = avg_return * annualization_factor if series.iloc[0] > 0 else None
    volatility = std_return * np.sqrt(252) if std_return > 0 else None
    sharpe = ((avg_return * annualization_factor) - risk_free_rate) / volatility if volatility and volatility > 0 else None

    # Max drawdown
    cum_returns = (1 + returns).cumprod()
    running_max = cum_returns.cummax()
    drawdown = (cum_returns - running_max) / running_max
    max_drawdown = float(drawdown.min()) if len(drawdown) > 0 else None

    return PerformanceResponse(
        total_return_pct=total_return * 100,
        annualized_return_pct=annualized_return * 100 if annualized_return else None,
        volatility_pct=volatility * 100 if volatility else None,
        sharpe_ratio=round(sharpe, 4) if sharpe else None,
        max_drawdown_pct=max_drawdown * 100 if max_drawdown else None,
    )
