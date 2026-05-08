from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional

from app.core.deps import get_current_user, get_db
from app.models.user import User
from app.services import options_service

router = APIRouter()


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


@router.post("/flow/scan")
async def trigger_scan(current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    count = await options_service.scan_unusual_activity(db, ["SPY", "QQQ", "AAPL", "MSFT", "AMZN", "TSLA", "NVDA", "META", "GOOGL"])
    return {"scanned": True, "events_found": count}
