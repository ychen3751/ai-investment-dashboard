from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional

from app.core.deps import get_current_user, get_db
from app.models.user import User
from app.services import options_chain_service, options_analysis_service, options_strategy_service
from app.services import options_service

router = APIRouter()


@router.get("/expirations")
async def get_expirations(symbol: str = Query(...)):
    """Available option expiration dates for a symbol."""
    return await options_chain_service.get_expirations(symbol)


@router.get("/chain")
async def get_option_chain(
    symbol: str = Query(...),
    expiration: Optional[str] = None,
    min_premium: float = Query(0, ge=0),
    option_type: Optional[str] = Query(None, pattern="^(call|put)$"),
    unusual_only: bool = False,
):
    """Option chain with unusual activity scoring for each contract.

    Scores range 0–100 based on volume/OI ratio, premium, moneyness,
    and time to expiration.  Data sourced from Yahoo Finance (delayed).
    """
    return await options_chain_service.get_chain_with_scores(
        symbol, expiration, min_premium, option_type, unusual_only
    )


@router.get("/flow/analysis")
async def get_flow_analysis(symbol: str = Query(...)):
    """AI-style options flow analysis for a ticker.

    Computes aggregate metrics (call/put volume, premium, IV, unusual activity)
    and applies a rule-based engine to determine bullish/bearish/neutral/mixed
    signal with supporting factors.  Educational purposes only — not financial
    advice.
    """
    return await options_analysis_service.get_flow_analysis(symbol)


# ── Legacy persistence-based endpoints (DB-backed) ───────────────────────


@router.get("/flow")
async def get_options_flow(
    symbol: Optional[str] = None,
    min_score: float = Query(50, ge=0, le=100),
    option_type: Optional[str] = None,
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Previously scanned unusual flow (persisted in DB)."""
    flows = await options_service.get_flow(db, symbol, min_score, option_type, limit, offset)
    return [
        {
            "id": str(f.id),
            "symbol": f.symbol,
            "option_type": f.option_type,
            "strike_price": float(f.strike_price),
            "expiration_date": str(f.expiration_date),
            "premium": float(f.premium),
            "volume": f.volume,
            "open_interest": f.open_interest,
            "volume_oi_ratio": float(f.volume_oi_ratio) if f.volume_oi_ratio else None,
            "unusual_score": float(f.unusual_score),
            "detected_at": f.detected_at.isoformat() if f.detected_at else None,
        }
        for f in flows
    ]


@router.get("/flow/stats")
async def get_flow_stats(current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    return await options_service.get_flow_stats(db)


@router.post("/strategy")
async def recommend_strategy(
    bias: str = "bullish",
    volatility: str = "moderate",
    risk_tolerance: str = "moderate",
    capital: float = 1000,
    time_horizon: str = "medium",
):
    """AI options strategy recommendation based on market outlook and risk tolerance.

    Educational only — not financial advice.
    """
    return await options_strategy_service.recommend_strategy(bias, volatility, risk_tolerance, capital, time_horizon)


@router.post("/flow/scan")
async def trigger_scan(current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    count = await options_service.scan_unusual_activity(db, ["SPY", "QQQ", "AAPL", "MSFT", "AMZN", "TSLA", "NVDA", "META", "GOOGL"])
    return {"scanned": True, "events_found": count}
