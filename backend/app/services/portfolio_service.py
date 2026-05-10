import uuid
from decimal import Decimal
from typing import List, Optional
from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from fastapi import HTTPException, status

from app.models.portfolio import Portfolio
from app.models.holding import Holding
from app.models.transaction import Transaction
from app.schemas.portfolio import PortfolioCreate, PortfolioResponse, HoldingResponse, PerformanceResponse, PortfolioSummary
from app.services import market_data_service


async def list_portfolios(db: AsyncSession, user_id: uuid.UUID) -> List[PortfolioResponse]:
    result = await db.execute(
        select(Portfolio).where(Portfolio.user_id == user_id).options(selectinload(Portfolio.holdings))
    )
    portfolios = result.scalars().all()
    responses = []
    for p in portfolios:
        resp = PortfolioResponse(
            id=p.id,
            name=p.name,
            description=p.description,
            created_at=p.created_at,
            updated_at=p.updated_at,
            holding_count=len(p.holdings),
        )
        total_value = Decimal("0")
        total_cost = Decimal("0")
        for h in p.holdings:
            quote = await market_data_service.get_quote(h.symbol)
            if quote and quote.get("price"):
                mv = Decimal(str(quote["price"])) * Decimal(str(h.quantity))
                total_value += mv
            total_cost += Decimal(str(h.average_cost_basis)) * Decimal(str(h.quantity))
        resp.total_cost = total_cost
        resp.total_value = total_value
        if total_cost > 0:
            resp.total_pnl = total_value - total_cost
            resp.total_pnl_pct = float((total_value - total_cost) / total_cost * 100)
        responses.append(resp)
    return responses


async def create_portfolio(db: AsyncSession, user_id: uuid.UUID, data: PortfolioCreate) -> Portfolio:
    portfolio = Portfolio(user_id=user_id, name=data.name, description=data.description)
    db.add(portfolio)
    await db.flush()
    await db.refresh(portfolio)
    return portfolio


async def get_portfolio(db: AsyncSession, user_id: uuid.UUID, portfolio_id: uuid.UUID) -> Portfolio:
    result = await db.execute(
        select(Portfolio).where(
            Portfolio.id == portfolio_id,
            Portfolio.user_id == user_id,
        ).options(selectinload(Portfolio.holdings))
    )
    portfolio = result.scalar_one_or_none()
    if not portfolio:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Portfolio not found")
    return portfolio


async def update_portfolio(db: AsyncSession, user_id: uuid.UUID, portfolio_id: uuid.UUID, data: PortfolioCreate) -> Portfolio:
    portfolio = await get_portfolio(db, user_id, portfolio_id)
    portfolio.name = data.name
    if data.description is not None:
        portfolio.description = data.description
    await db.flush()
    await db.refresh(portfolio)
    return portfolio


async def delete_portfolio(db: AsyncSession, user_id: uuid.UUID, portfolio_id: uuid.UUID):
    portfolio = await get_portfolio(db, user_id, portfolio_id)
    await db.delete(portfolio)
    await db.flush()


async def add_holding(db: AsyncSession, portfolio_id: uuid.UUID, symbol: str, quantity: Decimal, avg_cost: Decimal) -> Holding:
    # Check if holding already exists for this symbol in this portfolio
    result = await db.execute(
        select(Holding).where(
            Holding.portfolio_id == portfolio_id,
            Holding.symbol == symbol,
        )
    )
    existing = result.scalar_one_or_none()
    if existing:
        # Update weighted average cost basis
        total_qty = Decimal(str(existing.quantity)) + quantity
        total_cost = (Decimal(str(existing.quantity)) * Decimal(str(existing.average_cost_basis))) + (quantity * avg_cost)
        existing.quantity = total_qty
        existing.average_cost_basis = total_cost / total_qty
        await db.flush()
        await db.refresh(existing)
        return existing
    else:
        holding = Holding(
            portfolio_id=portfolio_id,
            symbol=symbol.upper(),
            quantity=quantity,
            average_cost_basis=avg_cost,
        )
        db.add(holding)
        await db.flush()
        await db.refresh(holding)
        return holding


async def remove_holding(db: AsyncSession, portfolio_id: uuid.UUID, holding_id: uuid.UUID):
    result = await db.execute(
        select(Holding).where(
            Holding.id == holding_id,
            Holding.portfolio_id == portfolio_id,
        )
    )
    holding = result.scalar_one_or_none()
    if not holding:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Holding not found")
    await db.delete(holding)
    await db.flush()


async def update_holding(db: AsyncSession, portfolio_id: uuid.UUID, holding_id: uuid.UUID, quantity: Decimal, avg_cost: Decimal) -> Holding:
    if quantity <= 0:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Quantity must be greater than 0")
    if avg_cost <= 0:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Average cost must be greater than 0")
    result = await db.execute(
        select(Holding).where(
            Holding.id == holding_id,
            Holding.portfolio_id == portfolio_id,
        )
    )
    holding = result.scalar_one_or_none()
    if not holding:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Holding not found")
    holding.quantity = quantity
    holding.average_cost_basis = avg_cost
    await db.flush()
    await db.refresh(holding)
    return holding


async def add_transaction(db: AsyncSession, portfolio_id: uuid.UUID, data) -> Transaction:
    transaction = Transaction(
        portfolio_id=portfolio_id,
        symbol=data.symbol.upper(),
        transaction_type=data.transaction_type,
        quantity=data.quantity,
        price=data.price,
        commission=data.commission,
        transaction_date=data.transaction_date,
        notes=data.notes,
    )
    db.add(transaction)

    # Auto-update holding
    qty = data.quantity if data.transaction_type == "BUY" else -data.quantity
    result = await db.execute(
        select(Holding).where(
            Holding.portfolio_id == portfolio_id,
            Holding.symbol == data.symbol.upper(),
        )
    )
    holding = result.scalar_one_or_none()
    if holding:
        new_qty = Decimal(str(holding.quantity)) + qty
        if new_qty <= 0:
            await db.delete(holding)
        else:
            holding.quantity = new_qty
    elif data.transaction_type == "BUY":
        holding = Holding(
            portfolio_id=portfolio_id,
            symbol=data.symbol.upper(),
            quantity=data.quantity,
            average_cost_basis=data.price,
        )
        db.add(holding)

    await db.flush()
    await db.refresh(transaction)
    return transaction


async def get_holdings_with_prices(db: AsyncSession, portfolio_id: uuid.UUID) -> List[HoldingResponse]:
    result = await db.execute(select(Holding).where(Holding.portfolio_id == portfolio_id))
    holdings = result.scalars().all()

    total_value = Decimal("0")
    responses = []
    for h in holdings:
        quote = await market_data_service.get_quote(h.symbol)
        current_price = Decimal(str(quote["price"])) if quote and quote.get("price") else None
        cost = Decimal(str(h.average_cost_basis)) * Decimal(str(h.quantity))
        mv = current_price * Decimal(str(h.quantity)) if current_price else None
        total_value += mv if mv else cost

        resp = HoldingResponse(
            id=h.id,
            symbol=h.symbol,
            quantity=Decimal(str(h.quantity)),
            average_cost_basis=Decimal(str(h.average_cost_basis)),
            current_price=current_price,
            day_change=Decimal(str(quote.get("change", 0))) if quote else None,
            day_change_pct=Decimal(str(quote.get("change_pct", 0))) if quote else None,
            market_value=mv,
            total_cost=cost,
            total_pnl=(mv - cost) if mv else None,
            total_pnl_pct=float((mv - cost) / cost * 100) if mv and cost > 0 else None,
            allocation_pct=0.0,
        )
        responses.append(resp)

    for r in responses:
        if total_value > 0 and r.market_value:
            r.allocation_pct = float(r.market_value / total_value * 100)

    return responses


async def get_portfolio_summary(db: AsyncSession, user_id: uuid.UUID) -> PortfolioSummary:
    result = await db.execute(
        select(Portfolio).where(Portfolio.user_id == user_id).options(
            selectinload(Portfolio.holdings), selectinload(Portfolio.option_positions)
        )
    )
    portfolios = result.scalars().all()

    total_value = Decimal("0")
    total_cost = Decimal("0")
    day_pnl = Decimal("0")
    holding_count = 0

    for p in portfolios:
        for h in p.holdings:
            holding_count += 1
            quote = await market_data_service.get_quote(h.symbol)
            cost = Decimal(str(h.average_cost_basis)) * Decimal(str(h.quantity))
            total_cost += cost
            if quote and quote.get("price"):
                mv = Decimal(str(quote["price"])) * Decimal(str(h.quantity))
                total_value += mv
                day_pnl += Decimal(str(quote.get("change", 0))) * Decimal(str(h.quantity))
                await market_data_service.add_tracked_symbol(h.symbol)

        # Option positions
        for opt in p.option_positions:
            contracts = int(opt.contracts)
            premium = float(opt.premium_per_contract)
            if opt.side == "long":
                total_cost += Decimal(str(premium * contracts * 100))
            try:
                chain = await market_data_service.get_info(opt.underlying_symbol)
            except Exception:
                pass  # option pricing best-effort

    return PortfolioSummary(
        total_value=total_value,
        total_cost=total_cost,
        total_pnl=total_value - total_cost,
        total_pnl_pct=float((total_value - total_cost) / total_cost * 100) if total_cost > 0 else 0,
        day_pnl=day_pnl,
        portfolio_count=len(portfolios),
        holding_count=holding_count,
    )
