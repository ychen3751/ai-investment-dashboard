from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_user, get_db
from app.models.user import User
from app.services import macro_service

router = APIRouter()


@router.get("/indices")
async def get_indices(current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    indices = await macro_service.get_indices(db)
    return [
        {
            "symbol": i.symbol,
            "name": i.name,
            "current_value": float(i.current_value) if i.current_value else None,
            "daily_change": float(i.daily_change) if i.daily_change else None,
            "daily_change_pct": float(i.daily_change_pct) if i.daily_change_pct else None,
        }
        for i in indices
    ]


@router.get("/sectors")
async def get_sectors(current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    sectors = await macro_service.get_sectors(db)
    return [
        {
            "name": s.sector_name,
            "daily_change_pct": float(s.daily_change_pct) if s.daily_change_pct else None,
            "ytd_change_pct": float(s.ytd_change_pct) if s.ytd_change_pct else None,
        }
        for s in sectors
    ]


@router.get("/economic")
async def get_economic_indicators(current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    indicators = await macro_service.get_economic_indicators(db)
    return [
        {
            "name": e.indicator_name,
            "value": float(e.value) if e.value else None,
            "previous_value": float(e.previous_value) if e.previous_value else None,
            "unit": e.unit,
        }
        for e in indicators
    ]
