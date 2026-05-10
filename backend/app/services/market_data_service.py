"""Backward-compatibility shim — delegates to market_service.

All existing call sites (portfolio_service, risk_service, technical_service,
alert_service, tasks) import from this module and keep working unchanged.
New code should import from app.services.market_service directly.
"""
from app.services.market_service import (
    add_tracked_symbol,
    get_fundamentals,
    get_history,
    get_info,
    get_quote,
    get_tracked_symbols,
    search_symbols,
)

__all__ = [
    "get_quote",
    "get_history",
    "get_info",
    "get_fundamentals",
    "search_symbols",
    "get_tracked_symbols",
    "add_tracked_symbol",
]
