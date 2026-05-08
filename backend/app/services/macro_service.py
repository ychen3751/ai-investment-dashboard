from typing import Any, Dict, List
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.external import yahoo_finance
from app.models.macro import MarketIndex, SectorPerformance, EconomicIndicator

INDICES = [
    ("SPY", "S&P 500 ETF"),
    ("QQQ", "Nasdaq 100 ETF"),
    ("DIA", "Dow Jones ETF"),
    ("IWM", "Russell 2000 ETF"),
]

SECTORS = [
    ("XLF", "Financials"),
    ("XLK", "Technology"),
    ("XLE", "Energy"),
    ("XLV", "Healthcare"),
    ("XLI", "Industrials"),
    ("XLY", "Consumer Cyclical"),
    ("XLP", "Consumer Defensive"),
    ("XLU", "Utilities"),
    ("XLB", "Materials"),
    ("XLRE", "Real Estate"),
    ("XLC", "Communication"),
]


async def update_indices(db: AsyncSession):
    for symbol, name in INDICES:
        try:
            quote = await yahoo_finance.get_quote(symbol)
            if not quote:
                continue
            result = await db.execute(select(MarketIndex).where(MarketIndex.symbol == symbol))
            idx = result.scalar_one_or_none()
            if idx:
                idx.current_value = quote.get("price")
                idx.daily_change = quote.get("change")
                idx.daily_change_pct = quote.get("change_pct")
            else:
                idx = MarketIndex(
                    symbol=symbol, name=name,
                    current_value=quote.get("price"),
                    daily_change=quote.get("change"),
                    daily_change_pct=quote.get("change_pct"),
                )
                db.add(idx)
        except Exception:
            continue
    await db.flush()


async def update_sectors(db: AsyncSession):
    for symbol, sector_name in SECTORS:
        try:
            quote = await yahoo_finance.get_quote(symbol)
            if not quote:
                continue
            result = await db.execute(select(SectorPerformance).where(SectorPerformance.sector_name == sector_name))
            sector = result.scalar_one_or_none()
            if sector:
                sector.daily_change_pct = quote.get("change_pct")
            else:
                sector = SectorPerformance(sector_name=sector_name, daily_change_pct=quote.get("change_pct"))
                db.add(sector)
        except Exception:
            continue
    await db.flush()


async def get_indices(db: AsyncSession) -> List[MarketIndex]:
    result = await db.execute(select(MarketIndex))
    return result.scalars().all()


async def get_sectors(db: AsyncSession) -> List[SectorPerformance]:
    result = await db.execute(select(SectorPerformance))
    return result.scalars().all()


async def get_economic_indicators(db: AsyncSession) -> List[EconomicIndicator]:
    result = await db.execute(select(EconomicIndicator))
    return result.scalars().all()
