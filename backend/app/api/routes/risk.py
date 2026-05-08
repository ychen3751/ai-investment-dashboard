import uuid
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Dict, Any

from app.core.deps import get_current_user, get_db
from app.models.user import User
from app.services import risk_service, portfolio_service

router = APIRouter()


@router.post("/var/{portfolio_id}")
async def calculate_var(portfolio_id: uuid.UUID, confidence: float = 0.95, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    portfolio = await portfolio_service.get_portfolio(db, current_user.id, portfolio_id)
    holdings = await portfolio_service.get_holdings_with_prices(db, portfolio_id)
    holdings_data = [{"symbol": h.symbol, "market_value": h.market_value or h.total_cost or 0} for h in holdings]
    result = await risk_service.calculate_var(holdings_data, confidence)
    await risk_service.save_calculation(db, portfolio_id, "var", {"confidence": confidence}, result)
    return result


@router.post("/beta/{portfolio_id}")
async def calculate_beta(portfolio_id: uuid.UUID, benchmark: str = "SPY", current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    portfolio = await portfolio_service.get_portfolio(db, current_user.id, portfolio_id)
    holdings = await portfolio_service.get_holdings_with_prices(db, portfolio_id)
    holdings_data = [{"symbol": h.symbol, "market_value": h.market_value or h.total_cost or 0} for h in holdings]
    result = await risk_service.calculate_beta(holdings_data, benchmark)
    await risk_service.save_calculation(db, portfolio_id, "beta", {"benchmark": benchmark}, result)
    return result


@router.post("/drawdown/{portfolio_id}")
async def calculate_drawdown(portfolio_id: uuid.UUID, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    portfolio = await portfolio_service.get_portfolio(db, current_user.id, portfolio_id)
    holdings = await portfolio_service.get_holdings_with_prices(db, portfolio_id)
    holdings_data = [{"symbol": h.symbol, "market_value": h.market_value or h.total_cost or 0} for h in holdings]
    result = await risk_service.calculate_drawdown(holdings_data)
    await risk_service.save_calculation(db, portfolio_id, "drawdown", {}, result)
    return result
