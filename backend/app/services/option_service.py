import uuid
from datetime import date, datetime
from decimal import Decimal
from typing import Any, Dict, List, Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException, status

from app.models.option_position import OptionPosition
from app.services import market_data_service

CONTRACT_MULTIPLIER = 100


async def list_options(db: AsyncSession, portfolio_id: uuid.UUID) -> List[Dict[str, Any]]:
    result = await db.execute(
        select(OptionPosition).where(OptionPosition.portfolio_id == portfolio_id)
    )
    options = result.scalars().all()
    return [await _enrich(db, opt) for opt in options]


async def create_option(
    db: AsyncSession, portfolio_id: uuid.UUID, data
) -> Dict[str, Any]:
    opt = OptionPosition(
        portfolio_id=portfolio_id,
        underlying_symbol=data.underlying_symbol.upper(),
        option_type=data.option_type,
        side=data.side,
        strike_price=data.strike_price,
        expiration_date=data.expiration_date,
        contracts=data.contracts,
        premium_per_contract=data.premium_per_contract,
    )
    db.add(opt)
    await db.flush()
    await db.refresh(opt)
    return await _enrich(db, opt)


async def update_option(
    db: AsyncSession, portfolio_id: uuid.UUID, option_id: uuid.UUID, data
) -> Dict[str, Any]:
    result = await db.execute(
        select(OptionPosition).where(
            OptionPosition.id == option_id,
            OptionPosition.portfolio_id == portfolio_id,
        )
    )
    opt = result.scalar_one_or_none()
    if not opt:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Option position not found")
    opt.contracts = data.contracts
    opt.premium_per_contract = data.premium_per_contract
    await db.flush()
    await db.refresh(opt)
    return await _enrich(db, opt)


async def delete_option(db: AsyncSession, portfolio_id: uuid.UUID, option_id: uuid.UUID):
    result = await db.execute(
        select(OptionPosition).where(
            OptionPosition.id == option_id,
            OptionPosition.portfolio_id == portfolio_id,
        )
    )
    opt = result.scalar_one_or_none()
    if not opt:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Option position not found")
    await db.delete(opt)
    await db.flush()


async def _enrich(db: AsyncSession, opt: OptionPosition) -> Dict[str, Any]:
    """Compute option metrics: cost basis, market value, P&L, status."""
    contracts = int(opt.contracts)
    premium = float(opt.premium_per_contract)

    # Cost basis: long = debit, short = credit
    if opt.side == "long":
        cost_basis = Decimal(str(premium * contracts * CONTRACT_MULTIPLIER))
    else:
        cost_basis = Decimal(str(premium * contracts * CONTRACT_MULTIPLIER))

    # Try to fetch current option price from yfinance
    current_price = None
    try:
        chain = await market_data_service.get_info(opt.underlying_symbol)
        # Fall back to manual: use yfinance options chain
        from app.external import yahoo_finance
        exp_str = opt.expiration_date.isoformat()
        chain_data = await yahoo_finance.get_options_chain(opt.underlying_symbol, exp_str)
        contracts_list = chain_data.get("calls" if opt.option_type == "call" else "puts", [])
        target_strike = float(opt.strike_price)
        for c in contracts_list:
            if abs(float(c["strike"]) - target_strike) < 0.01:
                current_price = Decimal(str(c["last_price"]))
                break
    except Exception:
        pass

    now = datetime.now()

    # Market value
    if current_price is not None:
        market_value = current_price * contracts * CONTRACT_MULTIPLIER
    else:
        market_value = None

    # P&L
    if market_value is not None and cost_basis is not None:
        if opt.side == "long":
            unrealized_pnl = market_value - cost_basis
        else:
            unrealized_pnl = cost_basis - market_value  # short: keep premium collected
        unrealized_pnl_pct = (
            float(unrealized_pnl) / float(cost_basis) * 100 if float(cost_basis) > 0 else 0
        )
    else:
        unrealized_pnl = None
        unrealized_pnl_pct = None

    # Status
    status = None
    expiry = opt.expiration_date
    today = date.today()
    if expiry < today:
        status = "Expired"
    elif (expiry - today).days <= 7:
        status = "Expiring Soon"
    else:
        # Check ITM/OTM — need stock price
        stock_price = None
        try:
            quote = await market_data_service.get_quote(opt.underlying_symbol)
            if quote:
                stock_price = float(quote.get("price", 0))
        except Exception:
            pass
        if stock_price and stock_price > 0:
            if opt.option_type == "call":
                status = "ITM" if stock_price > float(opt.strike_price) else "OTM"
            else:
                status = "ITM" if stock_price < float(opt.strike_price) else "OTM"

    return {
        "id": opt.id,
        "underlying_symbol": opt.underlying_symbol,
        "option_type": opt.option_type,
        "side": opt.side,
        "strike_price": opt.strike_price,
        "expiration_date": opt.expiration_date,
        "contracts": opt.contracts,
        "premium_per_contract": opt.premium_per_contract,
        "cost_basis": cost_basis,
        "market_value": market_value,
        "current_price": current_price,
        "unrealized_pnl": unrealized_pnl,
        "unrealized_pnl_pct": unrealized_pnl_pct,
        "status": status,
        "created_at": opt.created_at,
        "updated_at": opt.updated_at,
    }
