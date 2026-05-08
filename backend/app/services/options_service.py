from datetime import datetime, timezone, date
from decimal import Decimal
from typing import Any, Dict, List, Optional
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.external import yahoo_finance
from app.models.options_flow import OptionsFlow


async def scan_unusual_activity(db: AsyncSession, symbols: List[str]) -> int:
    """Scan option chains for unusual activity and store results."""
    count = 0
    now = datetime.now(timezone.utc)
    today = date.today()

    for symbol in symbols:
        try:
            chain = await yahoo_finance.get_options_chain(symbol)
            if not chain.get("calls") and not chain.get("puts"):
                continue

            all_contracts = [(c, "CALL") for c in chain.get("calls", [])] + \
                            [(c, "PUT") for c in chain.get("puts", [])]

            for contract, opt_type in all_contracts:
                volume = contract.get("volume", 0) or 0
                oi = contract.get("open_interest", 0) or 0
                premium = contract.get("premium", 0) or 0
                vol_oi_ratio = volume / max(oi, 1)

                # Calculate unusual score
                score = min(100, (vol_oi_ratio - 1) * 30 + (premium / 100000))
                if score < 50:
                    continue

                flow = OptionsFlow(
                    symbol=symbol.upper(),
                    option_type=opt_type,
                    strike_price=Decimal(str(contract.get("strike", 0))),
                    expiration_date=today,
                    premium=Decimal(str(premium)),
                    volume=volume,
                    open_interest=oi,
                    volume_oi_ratio=Decimal(str(vol_oi_ratio)),
                    unusual_score=Decimal(str(score)),
                    detected_at=now,
                )
                db.add(flow)
                count += 1

            if count >= 50:
                break
        except Exception:
            continue

    await db.flush()
    return count


async def get_flow(db: AsyncSession, symbol: Optional[str] = None, min_score: float = 50,
                   option_type: Optional[str] = None, limit: int = 50, offset: int = 0) -> List[OptionsFlow]:
    query = select(OptionsFlow).where(OptionsFlow.unusual_score >= min_score)
    if symbol:
        query = query.where(OptionsFlow.symbol == symbol.upper())
    if option_type:
        query = query.where(OptionsFlow.option_type == option_type)
    query = query.order_by(OptionsFlow.unusual_score.desc()).offset(offset).limit(limit)
    result = await db.execute(query)
    return result.scalars().all()


async def get_flow_stats(db: AsyncSession) -> Dict[str, Any]:
    today = date.today()
    result = await db.execute(
        select(
            func.count(OptionsFlow.id),
            func.sum(OptionsFlow.premium),
            func.avg(OptionsFlow.unusual_score),
        ).where(func.date(OptionsFlow.detected_at) == today)
    )
    row = result.one()
    total_events = row[0] or 0
    total_premium = float(row[1] or 0)
    avg_score = float(row[2] or 0)

    put_call = await db.execute(
        select(
            func.sum(func.case((OptionsFlow.option_type == 'PUT', 1), else_=0)),
            func.sum(func.case((OptionsFlow.option_type == 'CALL', 1), else_=0)),
        ).where(func.date(OptionsFlow.detected_at) == today)
    )
    pc_row = put_call.one()
    puts = float(pc_row[0] or 0)
    calls = float(pc_row[1] or 0)
    pc_ratio = round(puts / max(calls, 1), 2)

    return {
        "total_events": total_events,
        "total_premium": total_premium,
        "avg_unusual_score": round(avg_score, 1),
        "put_call_ratio": pc_ratio,
        "put_count": int(puts),
        "call_count": int(calls),
    }
