from datetime import date, timedelta
from typing import Any, Dict, List, Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.external import yahoo_finance
from app.models.earnings import EarningsCalendar, EarningsReport


async def update_calendar(db: AsyncSession) -> int:
    """Fetch upcoming earnings from Yahoo Finance and upsert into calendar."""
    count = 0
    for symbol in ["AAPL", "MSFT", "GOOGL", "AMZN", "META", "NVDA", "TSLA", "JPM", "V", "JNJ"]:
        try:
            info = await yahoo_finance.get_info(symbol)
            if not info:
                continue
            earnings = info.get("earningsDate")
            eps_est = info.get("epsTrailingTwelveMonths")

            if earnings:
                for dt in earnings:
                    if isinstance(dt, (int, float)):
                        report_date = date.fromtimestamp(dt)
                        existing = await db.execute(
                            select(EarningsCalendar).where(
                                EarningsCalendar.symbol == symbol,
                                EarningsCalendar.report_date == report_date,
                            )
                        )
                        if not existing.scalar_one_or_none():
                            cal = EarningsCalendar(
                                symbol=symbol,
                                report_date=report_date,
                                eps_estimate=eps_est,
                            )
                            db.add(cal)
                            count += 1
        except Exception:
            continue

    await db.flush()
    return count


async def get_calendar(db: AsyncSession, from_date: date, to_date: date, symbols: Optional[List[str]] = None) -> List[EarningsCalendar]:
    query = select(EarningsCalendar).where(
        EarningsCalendar.report_date >= from_date,
        EarningsCalendar.report_date <= to_date,
    )
    if symbols:
        query = query.where(EarningsCalendar.symbol.in_([s.upper() for s in symbols]))
    query = query.order_by(EarningsCalendar.report_date)
    result = await db.execute(query)
    return result.scalars().all()


async def get_earnings_history(db: AsyncSession, symbol: str) -> List[EarningsReport]:
    result = await db.execute(
        select(EarningsReport).where(EarningsReport.symbol == symbol.upper()).order_by(EarningsReport.report_date.desc()).limit(12)
    )
    return result.scalars().all()
