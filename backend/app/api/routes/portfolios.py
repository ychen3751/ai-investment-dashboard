import uuid
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

from app.core.deps import get_current_user, get_db
from app.models.user import User
from app.schemas.portfolio import (
    PortfolioCreate, PortfolioResponse, HoldingCreate, HoldingUpdate, HoldingResponse,
    TransactionCreate, TransactionResponse, PerformanceResponse, PortfolioSummary,
)
from app.services import portfolio_service

router = APIRouter()


@router.get("/summary", response_model=PortfolioSummary)
async def get_summary(current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    return await portfolio_service.get_portfolio_summary(db, current_user.id)


@router.get("", response_model=List[PortfolioResponse])
async def list_portfolios(current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    return await portfolio_service.list_portfolios(db, current_user.id)


@router.post("", response_model=PortfolioResponse, status_code=201)
async def create_portfolio(data: PortfolioCreate, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    portfolio = await portfolio_service.create_portfolio(db, current_user.id, data)
    return PortfolioResponse(id=portfolio.id, name=portfolio.name, description=portfolio.description, created_at=portfolio.created_at, updated_at=portfolio.updated_at)


@router.get("/{portfolio_id}", response_model=PortfolioResponse)
async def get_portfolio(portfolio_id: uuid.UUID, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    portfolio = await portfolio_service.get_portfolio(db, current_user.id, portfolio_id)
    holdings = await portfolio_service.get_holdings_with_prices(db, portfolio_id)
    total_value = sum((h.market_value or h.total_cost or 0) for h in holdings)
    total_cost = sum((h.total_cost or 0) for h in holdings)
    return PortfolioResponse(
        id=portfolio.id, name=portfolio.name, description=portfolio.description,
        created_at=portfolio.created_at, updated_at=portfolio.updated_at,
        total_value=total_value, total_cost=total_cost,
        total_pnl=total_value - total_cost,
        total_pnl_pct=float((total_value - total_cost) / total_cost * 100) if total_cost > 0 else 0,
        holding_count=len(holdings),
    )


@router.put("/{portfolio_id}", response_model=PortfolioResponse)
async def update_portfolio(portfolio_id: uuid.UUID, data: PortfolioCreate, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    portfolio = await portfolio_service.update_portfolio(db, current_user.id, portfolio_id, data)
    return PortfolioResponse(id=portfolio.id, name=portfolio.name, description=portfolio.description, created_at=portfolio.created_at, updated_at=portfolio.updated_at)


@router.delete("/{portfolio_id}", status_code=204)
async def delete_portfolio(portfolio_id: uuid.UUID, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    await portfolio_service.delete_portfolio(db, current_user.id, portfolio_id)


@router.get("/{portfolio_id}/holdings", response_model=List[HoldingResponse])
async def list_holdings(portfolio_id: uuid.UUID, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    await portfolio_service.get_portfolio(db, current_user.id, portfolio_id)  # verify ownership
    return await portfolio_service.get_holdings_with_prices(db, portfolio_id)


@router.post("/{portfolio_id}/holdings", response_model=HoldingResponse, status_code=201)
async def add_holding(portfolio_id: uuid.UUID, data: HoldingCreate, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    await portfolio_service.get_portfolio(db, current_user.id, portfolio_id)
    holding = await portfolio_service.add_holding(db, portfolio_id, data.symbol, data.quantity, data.average_cost_basis)
    holdings = await portfolio_service.get_holdings_with_prices(db, portfolio_id)
    for h in holdings:
        if h.id == holding.id:
            return h


@router.put("/{portfolio_id}/holdings/{holding_id}", response_model=HoldingResponse)
async def update_holding(portfolio_id: uuid.UUID, holding_id: uuid.UUID, data: HoldingUpdate, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    await portfolio_service.get_portfolio(db, current_user.id, portfolio_id)
    holding = await portfolio_service.update_holding(db, portfolio_id, holding_id, data.quantity, data.average_cost_basis)
    holdings = await portfolio_service.get_holdings_with_prices(db, portfolio_id)
    for h in holdings:
        if h.id == holding.id:
            return h


@router.delete("/{portfolio_id}/holdings/{holding_id}", status_code=204)
async def remove_holding(portfolio_id: uuid.UUID, holding_id: uuid.UUID, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    await portfolio_service.get_portfolio(db, current_user.id, portfolio_id)
    await portfolio_service.remove_holding(db, portfolio_id, holding_id)


@router.get("/{portfolio_id}/transactions", response_model=List[TransactionResponse])
async def list_transactions(portfolio_id: uuid.UUID, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    from sqlalchemy import select
    from app.models.transaction import Transaction
    await portfolio_service.get_portfolio(db, current_user.id, portfolio_id)
    result = await db.execute(select(Transaction).where(Transaction.portfolio_id == portfolio_id).order_by(Transaction.transaction_date.desc()))
    return result.scalars().all()


@router.post("/{portfolio_id}/transactions", response_model=TransactionResponse, status_code=201)
async def add_transaction(portfolio_id: uuid.UUID, data: TransactionCreate, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    await portfolio_service.get_portfolio(db, current_user.id, portfolio_id)
    return await portfolio_service.add_transaction(db, portfolio_id, data)


@router.get("/{portfolio_id}/performance", response_model=PerformanceResponse)
async def get_performance(portfolio_id: uuid.UUID, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    await portfolio_service.get_portfolio(db, current_user.id, portfolio_id)
    holdings = await portfolio_service.get_holdings_with_prices(db, portfolio_id)
    if not holdings:
        return PerformanceResponse()

    total_value = sum(float(h.market_value or 0) for h in holdings)
    if total_value <= 0:
        return PerformanceResponse()

    histories = []
    weights = []
    for h in holdings:
        history = await portfolio_service.market_data_service.get_history(h.symbol, "1d", "1y")
        if history and len(history) >= 2:
            histories.append([p["close"] for p in history])
            weights.append(float(h.market_value or 0) / total_value)

    if not histories:
        return PerformanceResponse()

    from app.services.performance_service import calculate_performance_from_weighted_returns
    return calculate_performance_from_weighted_returns(histories, weights)
