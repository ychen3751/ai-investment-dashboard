from datetime import date, timedelta
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional

from app.core.deps import get_current_user, get_db
from app.models.user import User
from app.services import earnings_service

router = APIRouter()


@router.get("/calendar")
async def get_calendar(
    days_ahead: int = Query(30, ge=1, le=90),
    symbols: Optional[str] = Query(None, description="Comma-separated symbols"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    from_date = date.today()
    to_date = date.today() + timedelta(days=days_ahead)
    symbol_list = [s.strip() for s in symbols.split(",")] if symbols else None
    events = await earnings_service.get_calendar(db, from_date, to_date, symbol_list)
    return [
        {
            "id": str(e.id),
            "symbol": e.symbol,
            "report_date": str(e.report_date),
            "fiscal_quarter": e.fiscal_quarter,
            "fiscal_year": e.fiscal_year,
            "eps_estimate": float(e.eps_estimate) if e.eps_estimate else None,
            "revenue_estimate": float(e.revenue_estimate) if e.revenue_estimate else None,
            "whisper_number": float(e.whisper_number) if e.whisper_number else None,
            "confirmed": e.confirmed,
        }
        for e in events
    ]


@router.get("/{symbol}/history")
async def get_earnings_history(symbol: str, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    reports = await earnings_service.get_earnings_history(db, symbol)
    return [
        {
            "symbol": r.symbol,
            "fiscal_quarter": r.fiscal_quarter,
            "fiscal_year": r.fiscal_year,
            "report_date": str(r.report_date),
            "eps_actual": float(r.eps_actual) if r.eps_actual else None,
            "eps_estimate": float(r.eps_estimate) if r.eps_estimate else None,
            "revenue_actual": float(r.revenue_actual) if r.revenue_actual else None,
            "revenue_estimate": float(r.revenue_estimate) if r.revenue_estimate else None,
            "eps_surprise_pct": round((float(r.eps_actual) - float(r.eps_estimate)) / abs(float(r.eps_estimate)) * 100, 2) if r.eps_actual and r.eps_estimate else None,
        }
        for r in reports
    ]
